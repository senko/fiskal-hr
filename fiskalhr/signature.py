from copy import deepcopy
from hashlib import md5
from os.path import exists
from typing import TYPE_CHECKING, Any, List, Optional
from uuid import uuid4

import xmlsec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from lxml import etree

if TYPE_CHECKING:
    from .ws import FiskalClient

SIGNATURE_FRAGMENT = """
 <Signature xmlns="http://www.w3.org/2000/09/xmldsig#">
     <SignedInfo>
       <CanonicalizationMethod Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#" />
       <SignatureMethod Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1" />
       <Reference>
         <Transforms>
           <Transform Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature" />
           <Transform Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"/>
         </Transforms>
         <DigestMethod Algorithm="http://www.w3.org/2000/09/xmldsig#sha1" />
         <DigestValue></DigestValue>
       </Reference>
     </SignedInfo>
     <SignatureValue/>
   </Signature>
"""


class SignatureError(Exception):
    pass


class Signer:
    def __init__(
        self,
        cert_path: str,
        key_path: Optional[str] = None,
        password: Optional[str] = None,
    ):
        if not key_path:
            key_path = cert_path

        self.xmlsec_key = self._load_xmlsec_key(key_path, password)
        self._load_xmlsec_cert(cert_path)
        self.signature_template = etree.fromstring(SIGNATURE_FRAGMENT)
        self.hazmat_key = self._load_hazmat_key(key_path, password)

    @staticmethod
    def _load_xmlsec_key(pem_path: str, password: Optional[str]) -> xmlsec.Key:
        if not exists(pem_path):
            raise ValueError("Company private key PEM file not found")

        try:
            key = xmlsec.Key.from_file(
                pem_path,
                xmlsec.KeyFormat.PEM,
                password=password,
            )
        except xmlsec.Error:
            raise ValueError("Cannot load private key")

        return key

    def _load_xmlsec_cert(self, pem_path: str) -> None:
        if not exists(pem_path):
            raise ValueError("Company certificate PEM file not found")

        try:
            self.xmlsec_key.load_cert_from_file(pem_path, xmlsec.KeyFormat.PEM)
        except xmlsec.Error:
            raise ValueError("Cannot load certificate")

    @staticmethod
    def _load_hazmat_key(pem_path: str, password: Optional[str]) -> Any:

        with open(pem_path, "rb") as key_file:
            return serialization.load_pem_private_key(
                key_file.read(),
                password=password.encode("utf-8") if password else None,
            )

    def sign_document(self, root) -> None:
        # add soap-env ns
        # nsmap = deepcopy(namespace_map)
        # nsmap.update(root.nsmap)

        req_node = root.find("{http://schemas.xmlsoap.org/soap/envelope/}Body/*")

        # Find the XML node with the request itself (eg. RacunZahtjev)
        if req_node is None:
            raise ValueError("Unable to find request tag element")

        request_id = str(uuid4())

        # The request node needs an Id so it can be referenced from the Reference node
        req_node.attrib["Id"] = request_id
        req_node.append(deepcopy(self.signature_template))

        sig_node = xmlsec.tree.find_node(req_node, xmlsec.constants.NodeSignature)

        # Set URI attribute of the Reference node to point to the request node
        ref_node = sig_node.find("SignedInfo/Reference", namespaces=sig_node.nsmap)
        ref_node.attrib["URI"] = f"#{request_id}"

        # Add required KeyInfo/X509Data information to the signature
        key_info = xmlsec.template.ensure_key_info(sig_node)
        x509_data = xmlsec.template.add_x509_data(key_info)
        xmlsec.template.x509_data_add_issuer_serial(x509_data)
        xmlsec.template.x509_data_add_certificate(x509_data)

        ctx = xmlsec.SignatureContext()
        ctx.key = self.xmlsec_key

        # Register <request_tag>.Id as a valid Id attribute so it can be used for
        # internal references (from Reference URI)
        ctx.register_id(req_node, id_attr="Id")

        # Signing will populate the Signature subtree in-place
        ctx.sign(sig_node)

    def sign_zki_payload(self, data: str) -> str:
        """
        Sign raw ZKI payload using the private key

        Payload is signed using SHA1+RSA algorithm. The signature is
        hashed using MD5 digest algorithm. The resulting digest is
        returned as hexadecimal string.

        See section 12 "Zaštitni kod izdavatelja" in the Fiskalizacija technical
        specification for the description of the algorithm.

        Args:
            * data - raw ZKI data to be signed

        Returns:
            * ZKI digest calculated the standard algorithm
        """

        # typing: ignore
        signature = self.hazmat_key.sign(
            data.encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA1(),
        )
        return md5(signature).hexdigest()


class Verifier:
    """ """

    def __init__(self, cert_path: str, ca_cert_paths: List[str]):
        if not exists(cert_path):
            raise ValueError(
                f"Fiskalizacija service certificate not found: {cert_path}"
            )
        try:
            self.key = xmlsec.Key.from_file(cert_path, xmlsec.KeyFormat.CERT_PEM, None)
        except xmlsec.Error:
            raise ValueError("Cannot load Fiskalizacija service certificate")
        self.manager = xmlsec.KeysManager()
        for ca_cert in ca_cert_paths:
            if not exists(ca_cert):
                raise ValueError(f"CA certificate not found: {ca_cert}")
            try:
                self.manager.load_cert(
                    ca_cert,
                    xmlsec.constants.KeyDataFormatPem,
                    xmlsec.constants.KeyDataTypeTrusted,
                )
            except xmlsec.Error:
                raise ValueError(f"Cannot load CA cert {ca_cert}")

    def verify_document(self, root):
        ctx = xmlsec.SignatureContext(manager=self.manager)
        ctx.key = self.key

        req_node = root.find("{http://schemas.xmlsoap.org/soap/envelope/}Body/*")
        ctx.register_id(req_node, "Id")

        sig_node = xmlsec.tree.find_node(root, xmlsec.constants.NodeSignature)

        try:
            ctx.verify(sig_node)
        except xmlsec.Error:
            raise SignatureError(f"Signature verification of {req_node.tag} failed")


class EnvelopedSignaturePlugin:
    def __init__(self, client: "FiskalClient", signer: Signer, verifier: Verifier):
        self.fiskal_client = client
        self.signer = signer
        self.verifier = verifier

    def egress(self, envelope, http_headers, operation, binding_options):
        if self.fiskal_client.requires_signature(operation):
            self.signer.sign_document(envelope)
        return envelope, http_headers

    def ingress(self, envelope, http_headers, operation):
        if self.fiskal_client.requires_signature(operation):
            self.verifier.verify_document(envelope)
        return envelope, http_headers

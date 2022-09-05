from base64 import b64decode
from unittest.mock import Mock

import pytest
from lxml import etree

from fiskalhr.signature import (
    EnvelopedSignaturePlugin,
    SignatureError,
    Signer,
    Verifier,
)

XML_TO_SIGN = """<?xml version='1.0' encoding='utf-8'?>
<soap-env:Envelope xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/">
    <soap-env:Body>
        <ns0:RacunZahtjev xmlns:ns0="http://www.apis-it.hr/fin/2012/types/f73" Id="RacunZahtjev">
            TEST
        </ns0:RacunZahtjev>
    </soap-env:Body>
</soap-env:Envelope>
"""
EMPTY_XML = """<?xml version='1.0' encoding='utf-8'?>
<soap-env:Envelope xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/">
    <soap-env:Body>
    </soap-env:Body>
</soap-env:Envelope>
"""


def test_signer_cert_not_found():
    with pytest.raises(ValueError):
        Signer("testdata/nonexistent", "testdata/client_plaintext.key")


def test_signer_cert_load_fails():
    with pytest.raises(ValueError):
        Signer("testdata/ws/wsdl/EmptyService.wsdl", "testdata/client_plaintext.key")


def test_signer_key_not_found():
    with pytest.raises(ValueError):
        Signer("testdata/client_combined.crt", "testdata/nonexistent")


def test_signer_key_load_fails():
    with pytest.raises(ValueError):
        Signer("testdata/client_combined.crt", "testdata/ws/wsdl/EmptyService.wsdl")


class TestSigner:
    @staticmethod
    def assert_doc_is_signed(doc):
        sig_el = doc.find("{*}Body/*/{*}Signature")
        assert sig_el is not None

        sig_hash_el = sig_el.find("{*}SignatureValue")
        assert sig_hash_el is not None

        # verify that the SignatureValue text is base64-encoded
        b64decode(sig_hash_el.text)

    def test_load_combined_encrypted_key(self):
        s = Signer(
            "testdata/client_combined_encrypted_key.crt",
            password="testdata",
        )
        doc = etree.fromstring(XML_TO_SIGN.encode("utf-8"))

        s.sign_document(doc)
        self.assert_doc_is_signed(doc)

        s.sign_zki_payload("123")

    def test_load_combined_plaintext_key(self):
        s = Signer("testdata/client_combined_plaintext_key.crt")
        doc = etree.fromstring(XML_TO_SIGN.encode("utf-8"))

        s.sign_document(doc)
        self.assert_doc_is_signed(doc)

        s.sign_zki_payload("123")

    def test_load_separate_encrypted_key(self):
        s = Signer(
            "testdata/client.crt",
            "testdata/client.key",
            "testdata",
        )
        doc = etree.fromstring(XML_TO_SIGN.encode("utf-8"))

        s.sign_document(doc)
        self.assert_doc_is_signed(doc)

        s.sign_zki_payload("123")

    def test_load_separate_plaintext_key(self):
        s = Signer(
            "testdata/client.crt",
            "testdata/client_plaintext.key",
        )
        doc = etree.fromstring(XML_TO_SIGN.encode("utf-8"))

        s.sign_document(doc)
        self.assert_doc_is_signed(doc)

        s.sign_zki_payload("123")

    def test_missing_request_tag_fails(self):
        s = Signer("testdata/client_combined_plaintext_key.crt")
        doc = etree.fromstring(EMPTY_XML.encode("utf-8"))

        with pytest.raises(ValueError):
            s.sign_document(doc)


def test_verifier_cert_not_found():
    with pytest.raises(ValueError):
        Verifier("testdata/nonexistent", [])


def test_verifier_cert_load_fails():
    with pytest.raises(ValueError):
        Verifier("testdata/ws/wsdl/EmptyService.wsdl", [])


def test_verifer_ca_certs_not_found():
    with pytest.raises(ValueError):
        Verifier("testdata/client.crt", ["testdata/nonexistent"])


def test_verifer_ca_cert_load_fails():
    with pytest.raises(ValueError):
        Verifier("testdata/client.crt", ["testdata/ws/wsdl/EmptyService.wsdl"])


class TestVerifier:
    def setup(self):
        signer = Signer(
            "testdata/client_combined_encrypted_key.crt",
            password="testdata",
        )
        self.doc = etree.fromstring(XML_TO_SIGN.encode("utf-8"))
        signer.sign_document(self.doc)

    def test_load_certs(self):
        verifier = Verifier("testdata/client.crt", ["testdata/root_ca.crt"])
        verifier.verify_document(self.doc)

    def test_load_combined(self):
        # FIXME - why does this work? client.crt should be untrusted
        verifier = Verifier("testdata/client.crt", [])
        verifier.verify_document(self.doc)

    def test_verification_fails_for_incorrect_certificate(self):
        verifier = Verifier("testdata/root_ca.crt", [])

        with pytest.raises(SignatureError):
            verifier.verify_document(self.doc)


class TestEnvelopedSignaturePlugin:
    def setup(self):
        self.client = Mock()
        self.signer = Mock()
        self.verifier = Mock()
        self.envelope = Mock()
        self.http_headers = Mock()
        self.operation = Mock()
        self.binding_options = Mock()
        self.plugin = EnvelopedSignaturePlugin(self.client, self.signer, self.verifier)

    def test_egress_no_signature(self):
        self.client.requires_signature.return_value = False

        self.plugin.egress(
            self.envelope,
            self.http_headers,
            self.operation,
            self.binding_options,
        )

        self.client.requires_signature.assert_called_once_with(self.operation)
        self.signer.sign_document.assert_not_called()

    def test_egress_with_signature(self):
        self.client.requires_signature.return_value = True

        self.plugin.egress(
            self.envelope,
            self.http_headers,
            self.operation,
            self.binding_options,
        )

        self.client.requires_signature.assert_called_once_with(self.operation)
        self.signer.sign_document.assert_called_once_with(self.envelope)

    def test_ingress_no_signature(self):
        self.client.requires_signature.return_value = False

        self.plugin.ingress(
            self.envelope,
            self.http_headers,
            self.operation,
        )

        self.client.requires_signature.assert_called_once_with(self.operation)
        self.verifier.verify_document.assert_not_called()

    def test_ingress_with_signature(self):
        self.client.requires_signature.return_value = True

        self.plugin.ingress(
            self.envelope,
            self.http_headers,
            self.operation,
        )

        self.client.requires_signature.assert_called_once_with(self.operation)
        self.verifier.verify_document.assert_called_once_with(self.envelope)

from datetime import datetime
from os.path import exists
from typing import TYPE_CHECKING, Any, Dict, Optional
from uuid import UUID, uuid4

from lxml import etree
from requests import Session
from zeep import Client
from zeep.exceptions import Fault
from zeep.transports import Transport
from zeep.wsdl.bindings.soap import SoapOperation

from .errors import ResponseError
from .signature import EnvelopedSignaturePlugin, Signer, Verifier

if TYPE_CHECKING:
    from .invoice import Document, Invoice, InvoicePaymentMethodChange


class FiskalClient:
    def __init__(
        self, ca_pem_path: str, wsdl_path: str, signer: Signer, verifier: Verifier
    ):
        """
        Client for Fiskalizacija SOAP web service

        Args:
          * ca_pem_path - FINA combined CA certificate
          * wsdl_path - Path to WSDL file defining the Fiskalizacija service
          * signer - request signature generator
          * verifier - response signature verifier
        """
        if not exists(ca_pem_path):
            raise ValueError("FINA combined CA certificate file not found")

        if not exists(wsdl_path):
            raise ValueError("Fiskalizacija WSDL file not found")

        session = Session()
        session.verify = ca_pem_path
        transport = Transport(session=session)

        plugin = EnvelopedSignaturePlugin(self, signer, verifier)
        self.client = Client(wsdl_path, transport=transport, plugins=[plugin])
        self.signer = signer
        self.verifier = verifier

        try:
            tns = [
                ns
                for (ns, url) in self.client.namespaces.items()
                if "apis-it.hr/fin/" in url
            ][0]
        except IndexError:
            existing_namespaces = ", ".join(
                url for url in self.client.namespaces.values()
            )
            raise ValueError(
                f"APIS IT WSDL namespace not found, defined namespaces: {existing_namespaces}"
            )

        self.type_factory = self.client.type_factory(tns)
        self.all_types = self._find_all_types()

    def _find_all_types(self):
        url_to_ns_map = {url: ns for (ns, url) in self.client.namespaces.items()}
        return {
            f"{url_to_ns_map[t.qname.namespace]}.{t.qname.localname}": t
            for t in self.client.wsdl.types.types
            if t.qname is not None
        }

    def requires_signature(self, operation: SoapOperation) -> bool:
        """
        Check whether the SOAP operation should be signed and response verified.

        This is an internal API for use by Signer and Verifier classes.

        Args:
            * operation - operation to check

        Returns:
            * True if operation should be signed/verified, False otherwise
        """

        return operation.name != "echo"

    def test_service(self, test_message: str = "ping"):
        """
        Test service integration using the "echo" service

        Args:
            * test_message - message to use
        """

        response = self.client.service.echo(test_message)
        if response != test_message:
            raise ValueError(
                f"Test echo service returned '{response}', expected '{test_message}'"
            )

    def create_request_header(
        self, message_id: Optional[UUID] = None, dt: Optional[datetime] = None
    ):
        """
        Create header (tns:Zaglavlje) to attach to the request

        Args:
            * message_id - unique message ID, or None to create a new random one
            * dt - date and time of the message, or None to use "now"
        """

        if message_id is None:
            message_id = uuid4()
        if dt is None:
            dt = datetime.now()

        return self.type_factory.ZaglavljeType(
            IdPoruke=message_id, DatumVrijeme=dt.strftime("%d.%m.%YT%H:%M:%S")
        )

    def _call_service(self, service_proxy, request_kwargs: Dict[str, Any]):
        try:
            return service_proxy(**request_kwargs)
        except Fault as fault:
            try:
                doc = etree.fromstring(fault.detail)
            except etree.XMLSyntaxError:
                raise ResponseError([])

            root = doc.find("{*}Body/*")
            if root is None:
                raise ResponseError([])

            fault_response = self.client.wsdl.types.deserialize(root)
            raise ResponseError.from_fault_response(fault_response)

    def check_invoice(self, invoice: "Invoice"):
        from .invoice import InvoiceWithDoc

        if not hasattr(self.client.service, "provjera"):
            raise RuntimeError("Check invoice operation is only available in demo mode")

        body = invoice.to_ws_object()
        request_kwargs = dict(Zaglavlje=self.create_request_header())

        if isinstance(invoice, InvoiceWithDoc):
            request_kwargs["RacunPD"] = body
        else:
            request_kwargs["Racun"] = body

        response = self._call_service(self.client.service.provjera, request_kwargs)

        return (
            response.RacunPD if isinstance(invoice, InvoiceWithDoc) else response.Racun
        )

    def submit_invoice(self, invoice: "Invoice") -> str:
        from .invoice import InvoiceWithDoc

        body = invoice.to_ws_object()
        request_kwargs = dict(Zaglavlje=self.create_request_header(), Racun=body)

        if isinstance(invoice, InvoiceWithDoc):
            service_proxy = self.client.service.racuniPD
        else:
            service_proxy = self.client.service.racuni

        response = self._call_service(service_proxy, request_kwargs)
        return response.Jir

    def change_payment_method(self, invoice: "InvoicePaymentMethodChange"):

        self._call_service(
            self.client.service.promijeniNacPlac,
            dict(
                Zaglavlje=self.create_request_header(),
                Racun=invoice.to_ws_object(),
            ),
        )

    def submit_document(self, doc: "Document") -> str:

        response = self._call_service(
            self.client.service.prateciDokumenti,
            dict(
                Zaglavlje=self.create_request_header(),
                PrateciDokument=doc.to_ws_object(),
            ),
        )

        return response.Jir

# Integrating with the Fiskalizacija service

Before you can integrate with the Croatian tax authority's Fiskalizacija
service, there are several preparation steps you need to do.

## Crash course into PKI

You'll need to know the basics of Public-Key Infrastructure
([PKI](https://www.keyfactor.com/resources/what-is-pki/)) technology to
get started.

To authenticate your client when connecting to the Fiskalizacija service,
you'll need a X.509 certificate (also just called "digital certificate")
and a corresponding private key. The certificate is public (you show it
around to anyone who asks), but the private key should never be shared
(it's how you prove you're the owner of that certificate).

The Fiskalizacija service will authenticate in the same way to you. It also
has a certificate you can check to know you're not talking to a scammer.

Both your certificate and the one the Fiskalizacija service uses are issued
by [FINA](https://www.fina.hr/fiskalizacija). FINA confirms the authenticity
of the certificates themselves (ie. proves that they aren't forged) by
signing them with it's own separate *root* certificate (you just have
to trust that one's the real thing).

Once you have your certificate and corresponding private key, you can
digitally sign your requests to the Fiskalizacija service. Similarly,
you can verify the responses are authentic using theirs certificate.

## Getting the certificates

### Obtain client certificates from FINA

Which certificates you need depends on whether you're developing and testing
integration (a "DEMO certificate"), or need it to go live and connect to
the service in production ("production certificate").

Production certificate can't be used for integration testing, so if you're
doing everything in-house (developing for own use and need to test the
integration), you'll need to sign up for both DEMO and production cert.

The certificates must be obtained from [FINA](https://www.fina.hr/fiskalizacija).

1. DEMO certificates

    Fill in the request form
    [Zahtjev za izdavanje Demo certifikata za fiskalizaciju](https://www.fina.hr/documents/52450/155573/7+Zahtjev+za+RDC_fiskalizacija+-+Demo_06092018.pdf/8c70682a-bd32-c32f-84f0-ce0441dba8ca)
    (PDF). You can send the request form  via email (alongside scans of your
    identity card), or file the request in person at any FINA office.

    The DEMO certificate is free.

2. Production certificates

    If you haven't already, you'll first need to register your company in FINA's
    PKI database. This will cost you about €10 (one-time fee) and you'll need to show
    [a few company registration documents](https://www.fina.hr/fiskalizacija#kako-do-certifikata).

    You'll also need to fill in
    [Zahtjev za izdavanje produkcijskog certifikata za fiskalizaciju](https://www.fina.hr/documents/52450/155573/ZahtjevCertFiskal.pdf/5a1b5509-378c-fb1f-ff7e-c95091dd2863?t=1600774713433) (one copy) and
    [Ugovor o obavljanju usluga certificiranja](https://rdc.fina.hr/obrasci/RDC-ugovor1.pdf)
    (two copies).

    The production certificate costs around €40 and is valid for 5 years.

### Download issued certificate

When you are issued the certificate, you'll get notified and will be able
to download it from FINA's [DEMO cert management page](https://demo-mojcert.fina.hr/finacms/).
Note that page first spends a minute trying to connect to a smart card reader,
before giving you an option to sign in with password you got in your
notification. If nothing seems to work, wait for a while.

During the download process, you'll be asked to choose a password that will be used to
encrypt the certificate. You'll decrypt it in the next step, but it is a good idea to write down
this password and store both the downloaded certificate and the password to a secure cold
location.

### Extract client certificate and key

The certificate you download will be in an encrypted binary PKCSv12 format. To decrypt it and
extract to a more manageable PEM format, use the `openssl` client library:

```
openssl pkcs12 --legacy -info -in Certifikat.p12 -nodes > combined-key-cert.pem
```

This will export the certificate and key into a PEM format. This is a text-based format
where each chunk of information is separated by delimiters like `-----BEGIN CERTIFICATE-----`
and `------END CERTIFICATE------`.

Both your certificate and private key are extracted to the same file. If you specify the
`-nodes` option (shown here), your private key will be unencrypted. If you omit that
option, you'll need to specify a key to encrypt the private key with (this can and should
be different than the password used to extract from PKVSv12 format). Note that in this
case you'll need to provide a password when using the private key.

The `fiskalhr` package supports both encrypted and plaintext key files. Moreover, they can
be bundled with your certificate in a single PEM file, or split into a separate file (eg.
`client.crt` for the certificate and `client.key` for the private key). Both are supported,
use what suits you best.

4. Download Porezna Uprava (tax authority) certificates

To connect to the Fiskalizacija service and verify responses, you'll need certificates
for Porezna Uprava. These also differ for DEMO and production environments.

To download the DEMO cert, go to [FINA's demo cert search page](http://demo-pki.fina.hr/certificate-search/?lang=hr)
and search for:

- Vrsta certifikata: aplikacijski certifikati
- Certifikacijsko tijelo (CA): FINA Demo CA 2020
- Naziv aplikacije ili sustava: fiskalcistest
- OIB: 02994650199

Production certificate is available from
[Porezna Uprava Fiskalizacija web page](https://www.porezna-uprava.hr/HR_Fiskalizacija/Stranice/Certifikati-za-preuzimanje.aspx).

5. Download FINA CA certificates

Since both your and Fiskalizacija's certificates are signed with FINA, you'll need to get
those as well. Again, these are separate for demo and production.

Demo certificaties can be found at [FINA DEMO CA certificates page](https://www.fina.hr/fina-demo-ca-certifikati).
You'll need the root CA and both 2020 and 2014 certificates.

Download the production certificates from the same
[Porezna Uprava Fiskalizacija web page](https://www.porezna-uprava.hr/HR_Fiskalizacija/Stranice/Certifikati-za-preuzimanje.aspx)
page where they host their own production certificates. You might need to download additional
certificates from the
[FINA CA (root) Certifikati](https://www.fina.hr/ca-fina-root-certifikati) page as well.

Note that for obscure technical reasons, FINA has two (or more) certificates for each
environment - the CA (possibly multiple) certs, and the *root* CA cert. To simplify management,
you can concatenate all of those into a certificate bundle:

```
cat FinaRootCA.cer FinaRDCCA2015.cer > fina-production-bundle.crt
```

## Download Fiskalizacija WSDL files

Connection to the Fiskalizacija service uses an XML-based protocol called SOAP. SOAP defines
the service operations (how requests must look, how responses must look, and how to connect)
in a WSDL file.

They can be downloaded from
[Porezna Uprava / Fiskalizacija / Tehničke specifikacije](https://www.porezna-uprava.hr/HR_Fiskalizacija/Stranice/Tehni%C4%8Dke-specifikacije.aspx)
page. Again, they are separate for demo and production use.

This package bundles with demo variant of the WSDL for internal testing purposes, but it is
recommended to download the latest demo certificate directly from the tax authorities' page.

## Register your point of sale location

Invoice numbers contain reference to the location where the invoice is created. In demo mode,
location code is ignored (you can specify whatever you want), but in production the code
*must* refer to the location that has been
[registered with the tax authority](https://www.porezna-uprava.hr/pozivni_centar/Stranice/Dostava-podataka-o-poslovnim-prostorima.aspx).

## Testing integration

Once you have the demo certificates and have installed `fiskalhr`, you should be able to
connect to the demo Fiskalizacija service and call a test "echo" service, which just
verifies that the connection is working:

```python
from fiskalhr.signature import Signer, Verifier
from fiskalhr.ws import FiskalClient

s = Signer("your-demo-cert.crt", "your-demo-key-unencrypted.key")
v = Verifier("fiskalcistest.pem", ["fina-demo-bundle.crt"])  # using PU's demo cert
f = FiskalClient("fina-demo-bundle.crt", "path/to/wsdl/FiskalizacijService.wsdl", s, v)

f.test_service()
```

If nothing happens (no errors), the communication is working. But the requests and
responses for this test service are not encrypted. To test that, add the following:

```python
from fiskalhr import Invoice

inv = Invoice(f)  # uses the FiskalClient instance from previous snippet

inv.invoice_number = InvoiceNumber("1/X/1")
inv.oib = "12345678903"  # note: the OIB here *MUST* match the certificate
inv.total = 100

f.check_invoice(inv)
```

Note that OIB used in your requests *must* match the OIB of the company the certificate
is issued to. This holds for both demo and production certificates.


## Troubleshooting

### Mixing production and demo certs

A common error is to mix up production and demo certificate. Note that for either environment, you'll need
completely separate certificates: root CA, FINA CA, Fiskalizacija and your certs.

To help with troubleshooting, you can use the `openssl` tool to inspect any certificate:

```
openssl x509 -text -in client.crt
```

Demo certs should have "demo" or "test" somewhere in their description.

### Plaintext vs encrypted key

Another error is to mix up plaintext and encrypted private key. You can distinguish them easily by
checking the file contents. The plaintext key file contains `BEGIN PRIVATE KEY` line, while the
encrypted key file contains `BEGIN ENCRYPTED PRIVATE KEY` line. The certificates are identified by
the `BEGIN CERTIFICATE` line. Certificates are always unecrypted (public).

### Enable xmlsec tracing

Sometimes it is useful to see low-level openssl debug messages while troubleshooting why a key
can't be loaded or a certificate isn't trusted. These can be enabled with:

```
import xmlsec
xmlsec.enable_debug_trace(True)
```

Note that these logs are really obscure and won't help you much unless you know how xmlsec and
OpenSSL work. But, if you need it, it's here.

### Enable request/response logging

You can enable logging of complete signed requests and responses from the service:

```python
import logging.config

logging.config.dictConfig(
    {
        "version": 1,
        "formatters": {"verbose": {"format": "%(name)s: %(message)s"}},
        "handlers": {
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "verbose",
            },
        },
        "loggers": {
            "zeep.transports": {
                "level": "DEBUG",
                "propagate": True,
                "handlers": ["console"],
            },
        },
    }
)
```

This is very verbose, so recommended to use only during debugging.

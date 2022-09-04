# fiskal-hr

Python 3 package for integrating with Croatian tax authority
[Fiskalizacija](https://www.porezna-uprava.hr/HR_Fiskalizacija/Stranice/FiskalizacijaNovo.aspx)
service.

## Scope

The package provides full integration with the Fiskalizacija service, including:

* checking invoice details in test (DEMO) mode - `FiskalClient.check_invoice()`
* submitting an invoice - `FiskalClient.submit_invoice()`
* submitting a fiscalization document - `FiskalClient.submit_document()`
* changing the payment method - `FiskalClient.change_payment_method()`

## Requirements

You'll need your client certificate, Fiskalizacija service certificate and FINA root CA
certificates. Read the [integration guide](doc/integration.md) for detailed steps how to
get and prepare the certificates.

You'll also need the `libxmlsec1` library installed on your computer.

## Quickstart

1. Install `fiskal-hr`:

    ```sh
    pip install fiskal-hr
    ```

2. Make sure you have your certificates ready, then initialize the fiskal client package:

    ```python
    from fiskalhr.invoice import Invoice
    from fiskalhr.ws import FiskalClient
    from fiskalhr.signature import Signer, Verifier

    signer = Signer("path/to/your-client-cert.pem")  # if encrypted, you'll need the password as well
    verifier = Verifier("path/to/service-cert.pem", ["path/to/fina-demo-ca-combined.pem"])
    fiskal_client = FiskalClient(
        "path/to/fina-demo-ca-combined.pem",
        "path/to/wsdl/FiskalizacijaService.wsdl",
        signer,
        verifier,
    )
    ```

3. Check communication with the service:

    ```python
    fiskal_client.test_service()
    ```

    This sends a "ping" message to the echo service, to check that basic connectivity is working.
    If there's an error, the `test_service()` method will raise an exception.

4. Create a test invoice and ask the service to do sanity checks on it (this only works in the
   demo mode):

    ```python
    invoice = Invoice(fiskal_client, oib="YOUR-OIB", invoice_number="1/X/1", total=100)

    fiskal_client.check_invoice(invoice)
    ```

    If there are any errors, the `check_invoice()` method will raise `fiskalhr.ResponseError`
    with the error details in the `details` attribute.

    Note that this does only basic sanity checking. For example, it will not check if the
    point of sale location (code `X` in the invoice number in this example) is registered.

## Testing

This package has 100% unit test coverage. To run the tests:

```
pytest
```

Coverage report is generated automatically. To export it in HTML form, run `coverage html`.

The tests do not contact Fiskalizacija service or any other external service, nor do they
require actual certificates. They are entirely self-contained.

More info about testing and certificates is available in [the testing guide](doc/tests.md).

## Contributing

Found a bug or think something can be improved? All contributions are welcome!

Before changing any code, please open a GitHub issue explaining what you'd like to do.
This will ensure that your planned contribution fits well with the rest of the package
and minimize the chance your pull request will be rejected.

If changing any code, please ensure that after your changes:

* all tests pass and the code coverage is still 100%
* `black`, `flake8` and `isort` find no problems
* the code doesn't depend on any external service

## License (MIT)

Copyright (C) 2022 by Senko Rasic <senko@senko.net>

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify, merge,
publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons
to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE
FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.

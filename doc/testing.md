# Testing fiskalhr

The package is extensively covered with a combination of unit and integrated tests.


## Automated tests

Run all the tests directly from the package root folder:

```
pytest
```

This will run all the tests, show test results and the coverage summary. The complete
coverage report is saved to `.coverage` and can be inspected using the `coverage` tool
(eg. `coverage html` to create an HTML report).

The tests bundle dummy test certificates and keys in the `testdata` folder. These
cannot be used to connect to the Fiskalizacija service in either demo (test)
or live (production) mode. The password for both root CA and client keys is
`testdata`.

The tests also bundle WSDL for Fiskalizacija demo service. These are used internally
to check WSDL handling, and can also be used to connect to the demo service when you
want to test your integration.

For production use, you should use the latest copy of production WSDL. All WSDL
files can be found at
[Porezna Uprava / Fiskalizacija / Tehničke specifikacije](https://www.porezna-uprava.hr/HR_Fiskalizacija/Stranice/Tehni%C4%8Dke-specifikacije.aspx)
web page.


## Regenerating test certificates

The bundled test certificates can be used as don't need to be regenerated.
However, if you ever want to, here's how to do it (use password `testdata` for
both root CA and client keys, since the tests expect it):

1. First, generate a self-signed root CA certificate and key:

    ```
    openssl req -x509 -sha256 -days 1825 -newkey rsa:2048 -keyout root_ca.key -out root_ca.crt
    ```

2. Then, generate a private key for the client:

    ```
    openssl genrsa -des3 -out client.key 2048
    ```

3. Decrypt client's private key (used for testing plaintext key loading)

    ```
    openssl rsa -in client.key -out client_plaintext.key
    ```

4. Generate certificate signing request (CSR) for the client

    ```
    openssl req -key client.key -new -out client.csr
    ```

5. Sign the CSR to generate the client certificate

    ```
    openssl x509 -req -CA root_ca.crt -CAkey root_ca.key -in client.csr -out client.crt -days 3650 -CAcreateserial
    ```

6. Generate combined certificate/key files (used for testing all cert loading combinations)

    ```
    cat client.crt root_ca.crt > client_combined.crt
    cat client.key client_combined.crt > client_combined_encrypted_key.crt
    cat client_plaintext.key client_combined.crt > client_combined_plaintext_key.crt
    ```

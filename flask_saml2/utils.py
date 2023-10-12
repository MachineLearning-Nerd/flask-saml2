import datetime
import pathlib
import typing as T
import uuid
from importlib import import_module
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, dsa, dh
import pytz

class cached_property(property):

    """A decorator that converts a function into a lazy property.
    The function wrapped is called the first time to retrieve the result
    and then that calculated result is used the next time you access the value:

    .. code-block:: python

        class Foo(object):
            @cached_property
            def foo(self):
                # calculate something important here
                return 42

    The class has to have a ``__dict__`` in order for this property to
    work.
    """

    # implementation detail: A subclass of python's builtin property
    # decorator, we override __get__ to check for a cached value. If one
    # chooses to invoke __get__ by hand the property will still work as
    # expected because the lookup logic is replicated in __get__ for
    # manual invocation.

    def __init__(self, func, name=None, doc=None):
        self.__name__ = name or func.__name__
        self.__module__ = func.__module__
        self.__doc__ = doc or func.__doc__
        self.func = func

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        _missing = object()
        value = obj.__dict__.get(self.__name__, _missing)
        if value is _missing:
            value = self.func(obj)
            obj.__dict__[self.__name__] = value
        return value

    def __set__(self, instance, value):
        raise AttributeError(f"Can not set read-only attribute {type(instance).__name__}.{self.name}")

    def __delete__(self, instance):
        raise AttributeError(f"Can not delete read-only attribute {type(instance).__name__}.{self.name}")


def import_string(path: str) -> T.Any:
    """
    Import a dotted Python path to a class or other module attribute.
    ``import_string('foo.bar.MyClass')`` will return the class ``MyClass`` from
    the package ``foo.bar``.
    """
    name, attr = path.rsplit('.', 1)
    return getattr(import_module(name), attr)


def get_random_id() -> str:
    """
    Generate a random ID string. The random ID will start with the '_'
    character.
    """
    # It is very important that these random IDs NOT start with a number.
    random_id = '_' + uuid.uuid4().hex
    return random_id


def utcnow() -> datetime.datetime:
    """Get the current time in UTC, as an aware :class:`datetime.datetime`."""
    return datetime.datetime.utcnow().replace(tzinfo=pytz.utc)



def certificate_to_string(certificate: x509.Certificate) -> str:
    """
    Take an x509 certificate and encode it to a string suitable for adding to
    XML responses.

    :param certificate: A certificate.
    """
    pem_bytes = certificate.public_bytes(encoding=serialization.Encoding.PEM)
    return pem_bytes.decode('utf-8')

def certificate_from_string(certificate: str, format=serialization.Encoding.PEM) -> x509.Certificate:
    """
    Load an X509 certificate from a string. This just parses the PEM-encoded string.

    :param certificate: A certificate string.
    :param format: The format of the certificate, from the serialization.Encoding class.
    """
    return x509.load_pem_x509_certificate(certificate.encode('utf-8'), default_backend())

def certificate_from_file(filename: str, format=serialization.Encoding.PEM) -> x509.Certificate:
    """Load an X509 certificate from ``filename``.

    :param filename: The path to the certificate on disk.
    :param format: The format of the certificate, from the serialization.Encoding class.
    """
    with open(filename, 'rb') as handle:
        return certificate_from_string(handle.read().decode('utf-8'), format)

def private_key_from_string(private_key: str, format=serialization.Encoding.PEM):
    """Load a private key from a string.

    :param private_key: A private key string.
    :param format: The format of the private key, from the serialization.Encoding class.
    """
    key = serialization.load_pem_private_key(private_key.encode('utf-8'), password=None, backend=default_backend())

    # Check the type of the key and handle accordingly
    if isinstance(key, rsa.RSAPrivateKey):
        return key
    elif isinstance(key, dsa.DSAPrivateKey):
        return key
    elif isinstance(key, dh.DHPrivateKey):
        return key
    else:
        raise ValueError("Unsupported private key type")

def private_key_from_file(filename: str, format=serialization.Encoding.PEM) -> serialization.NoEncryption:
    """Load a private key from ``filename``.

    :param filename: The path to the private key on disk.
    :param format: The format of the private key, from the serialization.Encoding class.
    """
    with open(filename, 'rb') as handle:
        return private_key_from_string(handle.read().decode('utf-8'), format)

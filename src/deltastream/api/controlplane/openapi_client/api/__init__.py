# flake8: noqa

if __import__("typing").TYPE_CHECKING:
    # import apis into api package
    from deltastream.api.controlplane.openapi_client.api.deltastream_api import DeltastreamApi
    
else:
    from lazy_imports import LazyModule, as_package, load

    load(
        LazyModule(
            *as_package(__file__),
            """# import apis into api package
from deltastream.api.controlplane.openapi_client.api.deltastream_api import DeltastreamApi

""",
            name=__name__,
            doc=__doc__,
        )
    )

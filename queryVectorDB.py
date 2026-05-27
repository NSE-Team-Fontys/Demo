from importlib import import_module

_cli = import_module("src.pipeline.03_retrieval.query_cli")

search = _cli.search
main = _cli.main


def __getattr__(name):
    return getattr(_cli, name)


__all__ = ["search", "main"]


if __name__ == "__main__":
    main()

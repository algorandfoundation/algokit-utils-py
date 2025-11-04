import argparse
import sys
from pathlib import Path

from oas_generator.builder import build_client_descriptor
from oas_generator.config import GeneratorConfig
from oas_generator.naming import IdentifierSanitizer
from oas_generator.parser import SpecParser
from oas_generator.renderer.engine import TemplateRenderer
from oas_generator.writer import write_files


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Python API clients from an OpenAPI spec")
    parser.add_argument("--spec", required=True, type=Path, help="Path to the OpenAPI spec JSON file")
    parser.add_argument(
        "--out",
        required=True,
        type=Path,
        help="Base output directory that contains generated packages (e.g. src)",
    )
    parser.add_argument(
        "--package", required=True, help="Package module path relative to --out (e.g. algokit_algod_client)"
    )
    parser.add_argument("--template-dir", type=Path, help="Optional path to override templates")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    parser = SpecParser()
    spec = parser.parse(args.spec)
    sanitizer = IdentifierSanitizer()
    config = GeneratorConfig(
        spec_path=args.spec,
        output_root=args.out,
        package_name=args.package,
        template_root=args.template_dir,
    )
    descriptor = build_client_descriptor(spec, args.package, sanitizer)
    renderer = TemplateRenderer(template_dir=args.template_dir)
    files = renderer.render(descriptor, config)
    write_files(files, config.target_package_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

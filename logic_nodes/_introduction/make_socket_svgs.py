"""This script creates .svg images of all socket types in COLORS."""

COLORS = {
    "action": "cc4c4c",
    "animation": "cccccc",
    "array": "cc6600",
    "bool": "cca6d6",
    "color": "c7c729",
    "dynamic": "63c763",
    "float": "a1a1a1",
    "integer": "0f8526",
    "object": "268cbf",
    "string": "70b2ff",
    "vector": "6363c7"
}


def main():
    with open("sockettype_template.svg", "r") as template:
        template_str = template.read()

    for socket_type, color in COLORS.items():
        with open(f"sockettype_{socket_type}.svg", "w") as f:
            f.write(template_str.replace("fill:#cc4c4c;", f"fill:#{color};"))


if __name__ == "__main__":
    main()

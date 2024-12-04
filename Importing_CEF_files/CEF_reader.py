import xml.etree.ElementTree as ET


def read_cef(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        return content
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return None


def parse_cef(content):
    try:
        root = ET.fromstring(content)
        return root
    except ET.ParseError as e:
        print(f"Error parsing CEF content: {e}")
        return None


def print_cef(root):
    if root is None:
        print("No content to display.")
        return

    for compound in root.iter("Compound"):
        mppid = compound.attrib.get("mppid")
        if mppid:
            print(f"ID: {mppid}")

    for location in root.iter("Location"):
        rt = location.attrib.get("rt")
        ccs = location.attrib.get("ccs")
        print(f"rt: {rt}, ccs: {ccs}")

    for mspeaks in root.iter("MSPeaks"):
        for peak in mspeaks:
            x = peak.attrib.get("x")
            y = peak.attrib.get("y")
            z = peak.attrib.get("z")
            s = peak.attrib.get("s")
            print(f"m/z: {x}, Intensity: {y}, Charge: {z}, Ion type: {s}")


# Example usage
file_path = "data/getting isotopic peaks to work/test CEF file.cef"
content = read_cef(file_path)
root = parse_cef(content)
print_cef(root)

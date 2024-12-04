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

    for mspeaks in root.iter("MSPeaks"):
        for peak in mspeaks:
            print(f"Tag: {peak.tag}, Attributes: {peak.attrib}, Text: {peak.text}")


# Example usage
file_path = "data/getting isotopic peaks to work/test CEF file.cef"
content = read_cef(file_path)
root = parse_cef(content)
print_cef(root)

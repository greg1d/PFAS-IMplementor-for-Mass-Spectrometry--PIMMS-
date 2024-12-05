import xml.etree.ElementTree as ET
import sqlite3


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


def clear_database(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS Compounds")
    cursor.execute("DROP TABLE IF EXISTS Locations")
    cursor.execute("DROP TABLE IF EXISTS MSPeaks")

    conn.commit()
    conn.close()


def store_data_in_db(root, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Compounds (
            id INTEGER PRIMARY KEY,
            mppid TEXT UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Locations (
            id INTEGER PRIMARY KEY,
            compound_id INTEGER,
            m REAL,
            rt REAL,
            ccs REAL,
            mz REAL,
            UNIQUE(compound_id, m, rt, ccs, mz),
            FOREIGN KEY (compound_id) REFERENCES Compounds (id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS MSPeaks (
            id INTEGER PRIMARY KEY,
            location_id INTEGER,
            x REAL,
            y REAL,
            z INTEGER,
            s TEXT,
            UNIQUE(location_id, x, y, z, s),
            FOREIGN KEY (location_id) REFERENCES Locations (id)
        )
    """)

    for compound in root.iter("Compound"):
        mppid = compound.attrib.get("mppid")
        cursor.execute("SELECT id FROM Compounds WHERE mppid = ?", (mppid,))
        compound_id = cursor.fetchone()

        if compound_id is None:
            cursor.execute("INSERT INTO Compounds (mppid) VALUES (?)", (mppid,))
            compound_id = cursor.lastrowid
        else:
            compound_id = compound_id[0]

        for location in compound.iter("Location"):
            m = location.attrib.get("m")
            rt = location.attrib.get("rt")
            ccs = location.attrib.get("ccs")
            mz = location.attrib.get("mz")
            cursor.execute(
                "SELECT id FROM Locations WHERE compound_id = ? AND m = ? AND rt = ? AND ccs = ? AND mz = ?",
                (compound_id, m, rt, ccs, mz),
            )
            location_id = cursor.fetchone()

            if location_id is None:
                cursor.execute(
                    "INSERT INTO Locations (compound_id, m, rt, ccs, mz) VALUES (?, ?, ?, ?, ?)",
                    (compound_id, m, rt, ccs, mz),
                )
                location_id = cursor.lastrowid
            else:
                location_id = location_id[0]

            for spectrum in compound.iter("Spectrum"):
                for mspeaks in spectrum.iter("MSPeaks"):
                    for peak in mspeaks.iter("p"):
                        x = peak.attrib.get("x")
                        y = peak.attrib.get("y")
                        z = peak.attrib.get("z")
                        s = peak.attrib.get("s")
                        cursor.execute(
                            "SELECT id FROM MSPeaks WHERE location_id = ? AND x = ? AND y = ? AND z = ? AND s = ?",
                            (location_id, x, y, z, s),
                        )
                        peak_id = cursor.fetchone()

                        if peak_id is None:
                            cursor.execute(
                                "INSERT INTO MSPeaks (location_id, x, y, z, s) VALUES (?, ?, ?, ?, ?)",
                                (location_id, x, y, z, s),
                            )

    conn.commit()
    conn.close()


def read_data_from_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Read data from Compounds table
    cursor.execute("SELECT * FROM Compounds")
    compounds = cursor.fetchall()
    print("Compounds:")
    for compound in compounds:
        print(compound)

    # Read data from Locations table
    cursor.execute("SELECT * FROM Locations")
    locations = cursor.fetchall()
    print("\nLocations:")
    for location in locations:
        print(location)

    # Read data from MSPeaks table
    cursor.execute("SELECT * FROM MSPeaks")
    mspeaks = cursor.fetchall()
    print("\nMSPeaks:")
    for peak in mspeaks:
        print(peak)

    conn.close()


# Example usage
file_path = "data/getting isotopic peaks to work/test CEF file.cef"
content = read_cef(file_path)
root = parse_cef(content)
clear_database("cef_data.db")
store_data_in_db(root, "cef_data.db")
read_data_from_db("cef_data.db")

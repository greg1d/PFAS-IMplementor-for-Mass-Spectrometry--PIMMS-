import os

# ✅ Get and print correct base directory
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# ✅ Stop BASE_DIR at "PIMMS v1.2"
while not os.path.basename(CURRENT_DIR).startswith("PIMMS v1.2"):
    CURRENT_DIR = os.path.dirname(CURRENT_DIR)

BASE_DIR = CURRENT_DIR  # Set BASE_DIR to "PIMMS v1.2"

# ✅ Print for debugging
print(f"[DEBUG] BASE_DIR is set to: {BASE_DIR}")

# ✅ File paths
STANDARDS_FILE = os.path.join(BASE_DIR, ".temp", "Standards_report.csv")
FILE_PATH = "PIMMS v1.2/Data_output/PIMMS Processed Data set.csv"
LIBRARY_PATH = (
    "PIMMS v1.2/import folder/Baker_Group_RPLC_DTIMS_MS_PFAS_Library_Negative.csv"
)
UPLOAD_FOLDER = os.path.join(BASE_DIR, "imported_libraries")
library_match_source = os.path.splitext(os.path.basename(LIBRARY_PATH))[0]
# ✅ Print paths for debugging


# ✅ Define Available Repeating Units (this is what was missing)
REPEATING_UNITS = {
    "CF2": 49.9968064,
    "OCF2": 65.9917214,
    "CF2CF2O": 115.988527,
    "CH2CF2": 64.012456,
    "HF": 20.0062278,
}

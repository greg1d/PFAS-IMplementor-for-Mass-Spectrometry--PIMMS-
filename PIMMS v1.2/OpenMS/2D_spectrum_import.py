import pyopenms as oms
import matplotlib.pyplot as plt

# Define the file path
mzml_file = r"D:\Twins Sample Run\Data\Demultiplexed\Raw\69 Paired 97.mzML"

# Create an MSExperiment object
exp = oms.MSExperiment()

# Load the mzML file into the MSExperiment object
oms.MzMLFile().load(mzml_file, exp)

# Look for the spectrum with scanId=141424
selected_spectrum = None

for spectrum in exp.getSpectra():
    if spectrum.getNativeID() == "scanId=141424":  # Match the scanId
        selected_spectrum = spectrum
        break

# Process the spectrum if found
if selected_spectrum:
    rt = selected_spectrum.getRT()  # Retention Time
    drift_time = (
        selected_spectrum.getDriftTime() if selected_spectrum.getDriftTime() else None
    )
    mz_values, intensity_values = selected_spectrum.get_peaks()

    print(
        f"✅ Found spectrum scanId=141424 with {len(mz_values)} peaks BEFORE centroiding."
    )

    # Check spectrum type
    if selected_spectrum.getType() == oms.SpectrumSettings.SpectrumType.CENTROID:
        print("⚠ This spectrum is ALREADY centroided. Skipping PeakPickerHiRes.")
        profile_spectra = None  # Do not attempt to centroid
    else:
        profile_spectra = oms.MSExperiment()
        profile_spectra.addSpectrum(selected_spectrum)  # Add to profile mode container

    # Apply peak picking if profile mode is found
    centroided_spectra = oms.MSExperiment()
    if profile_spectra:
        oms.PeakPickerHiRes().pickExperiment(profile_spectra, centroided_spectra, True)
        print(
            f"✅ {len(centroided_spectra.getSpectra())} spectra successfully centroided."
        )
    else:
        centroided_spectra.addSpectrum(
            selected_spectrum
        )  # If already centroided, reuse

    # Extract centroided peaks
    centroid_mz, centroid_intensity = centroided_spectra[0].get_peaks()

    print(f"✅ Spectrum now contains {len(centroid_mz)} peaks AFTER centroiding.")

    # Plot the centroided spectrum
    plt.figure(figsize=(10, 5))
    plt.xlim(0, 1500)  # into isotopic pattern
    plt.stem(centroid_mz, centroid_intensity)  # Remove the problematic argument

    plt.xlabel("m/z")
    plt.ylabel("Intensity")
    plt.title("Centroided Spectrum (Zoomed: 771.8 - 774 m/z) - scanId=141424")
    plt.grid(True)
    plt.show()

else:
    print("⚠ Spectrum with scanId=141424 not found in the mzML file.")

import pyopenms as oms
import pandas as pd

exp = oms.MSExperiment()
oms.MzMLFile().load("D:\Twins Sample Run\Data\Demultiplexed\Raw\80 DB.mzML", exp)


drift_times = []
retention_times = []
mz_values = []

for i, spectrum in enumerate(exp.getSpectra()[:10]):
    drift_time = spectrum.getDriftTime()
    rt = spectrum.getRT()

    drift_times.append(drift_time)
    retention_times.append(rt)

df = pd.DataFrame(
    {
        "Spectrum Number": range(1, len(drift_times) + 1),
        "Drift Time (ms)": drift_times,
        "Retention Time (sec)": retention_times,
    }
)

print("\nFirst 10 spectra:")
print(df.head(5))

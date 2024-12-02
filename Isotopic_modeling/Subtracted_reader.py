import pandas as pd


def main():
    # Read the CSV file
    df = pd.read_csv("data\Edited full blank subtracted data set.csv")

    # Sort the DataFrame by the "m/z" column
    df = df.sort_values(by="m/z")

    # Extract the "m/z", "RT", and "CCS" columns as lists
    array = df["m/z"].tolist()
    rt_array = df["RT"].tolist()
    ccs_array = df["CCS"].tolist()

    z_range = range(1, 4)  # User-defined range for z from 1 to 3

    identified_features = set()
    groups = []

    for i in range(len(array)):
        if array[i] not in identified_features:
            group = expand_group(
                array, rt_array, ccs_array, array[i], rt_array[i], ccs_array[i], z_range
            )
            if len(group) >= 2:  # Only add groups with more than 2 features
                groups.append(group)
                identified_features.update(group)

    print(f"Number of groups identified: {len(groups)}")

    print("Groups of related peaks:")
    for group in groups:
        if len(group) >= 2:
            print(f"Group: {sorted(group)}")

    total_features = len(array)
    grouped_features = sum(len(group) for group in groups if len(group) >= 2)
    unrelated_features = total_features - grouped_features

    print(
        f"Number of unrelated features: {unrelated_features}"
    )  # Print the identified features


if __name__ == "__main__":
    main()

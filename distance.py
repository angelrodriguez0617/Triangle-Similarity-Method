import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
# The Medium Tele Camera of the DJI Mavic 3 Pro has an 
# image sensor of 1/1.3″ CMOS with a Real Focal Length of 19.4mm and an Equivalent Focal Length of 70mm.
# https://forum.dji.com/thread-299162-1-1.html

# Zenmuse H20T Wide specs
# SENSORHT = 4.87 # Millimeters
# SENSORHTPX = 1080 # Pixels ## Specific to video capture
# FOCAL = 4.5 # Millimeters
# ---------------------------
# H20T Zoom 1x specs
SENSORHT = 5.59 # Millimeters
SENSORHTPX = 1080 # Pixels ## Specific to video capture ## 2160 or 1080
FOCAL = 6.83 # Millimeters
# ---------------------------
# H20T Mavic 3T Wide specs
# Specs found from generic lookup table since Focal Length is not given by manufacturer
# SENSORHT = 4.8 # Millimeters
# SENSORHTPX = 1080 # Pixels ## Specific to video capture ## 2160 or 1080
# FOCAL = 2.86 # Millimeters
# ---------------------------
# Turbine
OBJHT = 1.01# Meters #TODO: Is this the best number?
OBJHT2 = .93# Meters #TODO: Is this the best number?

experiments = pd.read_sql_table("DistanceExperiment", "sqlite:///distance.db")
samples = pd.read_sql_table("DistanceExperimentSample", "sqlite:///distance.db")
# Changed right joins to left joins, Sqlite3 does not seem to support right joins any more?
# sqlite3.OperationalError: RIGHT and FULL OUTER JOINs are not currently supported
combined = pd.read_sql(
    "select * from DistanceExperimentSample des LEFT JOIN DistanceExperiment de on des.distanceExperimentId=de.idx",
    "sqlite:///distance.db",
)
# averageSize = pd.read_sql(
#     """select de.*, avg(des.width) as width, avg(des.height) as height from
#                           DistanceExperiment de RIGHT JOIN DistanceExperimentSample des
#                           on de.idx=des.distanceExperimentId
#                           group by de.idx""",
#     "sqlite:///distance.db",
# )
averageMaxDimension = pd.read_sql(
    """select de.*, avg(case when des.width > des.height then des.width else des.height end) as maxDimension from
                          DistanceExperimentSample des LEFT JOIN DistanceExperiment de
                          on des.distanceExperimentId=de.idx
                          group by de.idx""",
    "sqlite:///distance.db",
)
# -----------------------------
# print(experiments)
# print(samples)
# print(combined)
# print(averageSize)
# print(averageMaxDimension)
# -----------------------------
def compute_distance(sensor_height_metric, sensor_height_pixels, object_height_metric, focal_length, object_height_pixels):
    obj_height_on_sensor_metric = sensor_height_metric * object_height_pixels / sensor_height_pixels
    return object_height_metric * focal_length / obj_height_on_sensor_metric

def get_plot(experiment_name, rotate=1):
    filtered_df = averageMaxDimension[
        (averageMaxDimension["name"].str.contains(experiment_name, case=False))
        & (averageMaxDimension["rotating"] == rotate)
        & (averageMaxDimension["numSamples"] == 200)
        & (averageMaxDimension["realDistance"] <= 10)
    ]

    filtered_df['Estimated'] = filtered_df.apply(lambda row: compute_distance(SENSORHT, SENSORHTPX, OBJHT, FOCAL, row['maxDimension']), axis=1)
    filtered_df['SecondEstimate'] = filtered_df.apply(lambda row: compute_distance(SENSORHT, SENSORHTPX, OBJHT2, FOCAL, row['maxDimension']), axis=1)
    print(filtered_df[["name", "realDistance", "maxDimension", "Estimated", "SecondEstimate"]])
    average_error_one = np.mean(filtered_df['Estimated'] - filtered_df['realDistance'])
    average_error_two = np.mean(filtered_df['SecondEstimate'] - filtered_df['realDistance'])
    print(f"Average Error with object height of {OBJHT}: {average_error_one}")
    print(f"Average Error with object height of {OBJHT2}: {average_error_two}")

    # Create a range of x values for the fitted line
    x_values = np.linspace(
        filtered_df["maxDimension"].min(), filtered_df["maxDimension"].max(), 100
    )

    # Calculate the corresponding y values for the fitted line
    y_values_one = compute_distance(SENSORHT, SENSORHTPX, OBJHT, FOCAL, x_values)
    y_values_two = compute_distance(SENSORHT, SENSORHTPX, OBJHT2, FOCAL, x_values)

    # Create a scatter plot of the original data
    plt.figure(figsize=(10, 6))
    plt.scatter(filtered_df["maxDimension"], filtered_df["realDistance"], label="Data", color = 'blue')

    # Plot the fitted line
    plt.plot(
        x_values,
        y_values_one,
        color="red",
        label=f"Computed using sensor dimensions, Object Height {OBJHT}",
    )
    plt.plot(
        x_values,
        y_values_two,
        color="green",
        label=f"Computed using sensor dimensions, Object Height {OBJHT2}",
    )
    plt.title(f"Real Distance vs Max Dimension: {experiment_name}")
    plt.xlabel("Max Dimension (pixels)")
    plt.ylabel("Real Distance (meters)")
    plt.legend()
    plt.grid(True)
    plt.show()
# get_plot("H20T Wide")
get_plot("H20T Zoom 1x")
# get_plot("Mavic 3T Wide")

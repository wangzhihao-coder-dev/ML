#######################################################################
#
# Handling and Cleaning Date/Time Data in R
#
#######################################################################

# Clear all variables from the environment to ensure a clean slate.
# This prevents old data from interfering with the current script.
rm(list = ls())

#######################################################################
# Step 1: Load and Inspect Initial Data
#
# For this script to work, a file named "SampleDateTimeData.csv" must
# exist in your R working directory.
#######################################################################

# Read the data from the CSV file into a data frame named 'rental.df'.
# 'header = TRUE' tells R that the first row of the file contains column names.
rental.df <- read.csv("SampleDateTimeData.csv", header = TRUE)

# Print the initial data frame to the console to see how R loaded it.
# Notice that the date columns are initially treated as character strings (text).
cat("--- 1. Data as read from CSV file ---\n")
print(rental.df)


#######################################################################
# Step 2: Convert Text to Proper R Date-Time Objects
#
# Date-time calculations can only be performed on specialized date-time
# objects, not on plain text. We use as.POSIXct() for this conversion.
#######################################################################

# Convert the 'Start.Date' column from text to POSIXct format.
# The 'format' argument is crucial: it tells R exactly how to read the
# input string (Day/Month/Year Hour:Minute).
rental.df$Start.Date <- as.POSIXct(rental.df$Start.Date, format = "%d/%m/%Y %H:%M")

# Do the same for the 'End.Date' column.
# If a date string does not match the specified format (e.g., "24/Oct/2023"),
# R cannot convert it and will produce an 'NA' (Not Available) value.
rental.df$End.Date   <- as.POSIXct(rental.df$End.Date,   format = "%d/%m/%Y %H:%M")

# Print the data frame again to show the converted columns.
# The dates are now in a standard format, and the malformed date is NA.
cat("\n--- 2. Data after converting to Date-Time format (note the NA) ---\n")
print(rental.df)

#######################################################################
# Step 3: Calculate Journey Durations
#
# The `difftime()` function calculates the difference between two
# POSIXct objects. We can specify the desired units for the result.
# Note: This initial calculation will show negative durations for
# journeys that cross midnight.
#######################################################################

# Calculate duration in hours.
# `with()` is a convenience function that lets us use column names directly
# without typing `rental.df$` repeatedly inside the function call.
# `as.numeric()` converts the special 'difftime' object into a simple number.
rental.df$Duration.in.Hrs <- with(rental.df,
                                  as.numeric(difftime(End.Date, Start.Date, units = "hours"))
)

# Calculate duration in minutes, following the same logic.
rental.df$Duration.in.Mins <- with(rental.df,
                                   as.numeric(difftime(End.Date, Start.Date, units = "mins"))
)

# Calculate duration in seconds.
rental.df$Duration.in.Secs <- with(rental.df,
                                   as.numeric(difftime(End.Date, Start.Date, units = "secs"))
)

# Display the first few rows to show the new duration columns.
# `head()` is a quick way to preview a data frame.
cat("\n--- 3. Data with calculated durations (note the negative value) ---\n")
print(head(rental.df))

#######################################################################
# Step 4: Extract Time of Day (ToD)
#
# This advanced step calculates the time of day (e.g., 14.5 for 2:30 PM)
# for both start and end times. This is useful for analyzing patterns,
# such as rush hour rentals. The logic is to find the time elapsed
# since midnight on the day of the event.
#######################################################################

# We define a helper function to make the process reusable and clean.
# This function takes any POSIXct object and returns a new POSIXct object
# representing midnight at the beginning of that same day.
getMidnightDt <- function(my.dt) {
  # `strftime` formats a date-time object into a string.
  # "%F" is a shortcut for the "%Y-%m-%d" format (e.g., "2023-10-21").
  date.str <- strftime(my.dt, format = "%F")
  
  # Append "00:00:00" to the date string to create a text representation of midnight.
  midnight.str <- paste(date.str, "00:00:00", sep = " ")
  
  # Convert this new "midnight string" back into a proper POSIXct object.
  midnight.dt  <- as.POSIXct(midnight.str, format = "%Y-%m-%d %H:%M:%S")
  
  # Return the final POSIXct object for midnight.
  return(midnight.dt)
}

# Now, apply this function to our data columns.
# `sapply()` applies the `getMidnightDt` function to every single element
# of the 'Start.Date' vector, returning a vector of corresponding midnights.
midnight.dts <- sapply(rental.df$Start.Date, getMidnightDt)

# Calculate the start Time-of-Day (ToD) by finding the difference in hours
# between the actual start time and the midnight of that day.
rental.df$Start.ToD <- as.numeric(difftime(rental.df$Start.Date, midnight.dts, units = "hours"))

# Repeat the entire process for the 'End.Date' column.
midnight.dts <- sapply(rental.df$End.Date, getMidnightDt)
rental.df$End.ToD <- as.numeric(difftime(rental.df$End.Date, midnight.dts, units = "hours"))

# Display the first few rows of the final data frame.
# You can now see the 'Start.ToD' and 'End.ToD' columns added.
cat("\n--- 4. Final data with Time-of-Day columns ---\n")
print(head(rental.df))


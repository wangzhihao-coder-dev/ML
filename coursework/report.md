# DATA70121 Coursework: EDA & Regression

<p class="meta">Student ID: {{STUDENT_ID}} &nbsp;|&nbsp; Main text: {{WORD_COUNT}} words (tables, figures, captions, references and appendix excluded)</p>

## 1. The data

`MavenRail.csv` is a synthetic dataset, adapted from a Maven Analytics data challenge, describing fictitious rail journeys in the UK between 1 January and 30 April 2024. Each of its 30,686 rows is one ticket for one journey, and its 13 columns record three kinds of information:

- **The ticket:** price in pounds (£1 to £267, median £11), class (Standard 90%, First Class 10%), type (Advance, Off-Peak or Anytime), payment method (credit card, contactless or debit card) and railcard (none 66%; otherwise Adult, Senior or Disabled).
- **The journey:** departure and arrival stations (12 origins, 32 destinations, 64 routes), departure time, and scheduled and actual arrival times.
- **The outcome:** journey status (87% on time, 7% delayed, 6% cancelled), the reason for any delay, and whether the passenger requested a refund (1,095 requests, 3.6%).

Q4 PLACEHOLDER

## References

<div class="refs" markdown="1">

Maven Analytics (2024) *UK Train Rides* [dataset]. Maven Analytics Data Playground. Available at: https://mavenanalytics.io/data-playground (Accessed: 12 November 2026).

</div>

# RIT Campus Sheets (Excel-ready)

These CSV files are ready to open in Excel.

## Files

- rit_campus_locations.csv: master place registry (buildings, rooms, offices, landmarks)
- rit_landmark_relations.csv: near/behind/next_to relations for natural language guidance
- rit_walk_paths.csv: graph edges for distance and ETA calculations

## How to use in Excel as one workbook

1. Open Excel.
2. Import each CSV file as a separate sheet:
   - Sheet 1: Locations
   - Sheet 2: Relations
   - Sheet 3: Paths
3. Save as `RIT_Campus_Navigation.xlsx`.

## Data quality fields

- verification_status values:
  - verified_public: known public-level data
  - needs_verification: must be confirmed by campus admin/facility team

## What to verify first

1. Exact coordinates for every block entrance
2. Floor and room mapping for each classroom
3. Walking paths and accessibility (stairs/lift)
4. Landmark relation accuracy (near/behind/opposite)

## Safe rollout rule

Use only rows with `verification_status=verified_public` for production responses until verification is complete.

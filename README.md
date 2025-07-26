
# BONI: Bookmarking Of Notable Intervals

<img src="boni.png" width="300px">

BONI is a video analysis tool designed for researchers and analysts to precisely mark and measure intervals of interest in video footage. The application allows users to define start and end keyframes, calculate time intervals between them, and record these observations for further analysis.

## Features

- **Drag & Drop Interface**: Easily load MP4 video files by dragging them into the application
- **Precise Keyframe Marking**: Set start and end keyframes with frame-level accuracy
- **Visual Feedback**: See thumbnails of both start and end keyframes
- **Time Interval Calculation**: Automatically calculates and displays the duration between keyframes
- **Keyboard Shortcuts**:
  - Spacebar: Play/Pause video
  - Ctrl+1: Set start keyframe
  - Ctrl+2: Set end keyframe
  - Ctrl+Enter: Record current interval
  - Arrow keys: Frame-by-frame navigation
- **Data Management**: Save and manage multiple observations per video file
- **Export Capabilities**: Copy observation data to clipboard for use in other applications

## System Requirements

- macOS (tested on Sonoma)
- Windows and Linux support (theoretically possible but not tested)

## Usage

1. Drag and drop MP4 video files into the right panel
2. Select a video file to analyze
3. Use the playback controls or arrow keys to navigate through the video
4. Set start and end keyframes using the buttons or keyboard shortcuts
5. Review the calculated time interval
6. Record observations using the Record button or Ctrl+Enter
7. Copy observation data to clipboard for analysis in spreadsheet applications

## Technical Notes

- The application uses PySide6 for the GUI interface
- OpenCV is used for precise frame capture and image processing
- All observation data is stored in memory during the session

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License.

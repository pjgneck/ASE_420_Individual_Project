# CommandManagerApp Unit Tests

This document explains the unit tests for the `CommandManagerApp` Python application, which manages commands and devices using a GUI (Tkinter + ttkbootstrap) and communicates with an API.

---

## Overview

The unit tests are designed to:

1. Verify that API interactions work correctly for fetching and sending data.
2. Ensure import and export functionality handles JSON files properly.
3. Validate that GUI elements, such as tables, refresh and filter correctly.
4. Avoid triggering real network requests, file dialogs, or message boxes by using mocks.

---

## Testing Frameworks

- **unittest**: Python’s built-in unit testing framework.
- **unittest.mock**: Used to mock API requests, file operations, and GUI dialogs.

---

## Test Categories

### 1. API Fetching

- Ensures that data is correctly retrieved from the API.
- Tests both successful responses and failure scenarios, including network errors.
- Confirms that the appropriate error messages are displayed on failures.

### 2. Sending Data

- Ensures that data is sent correctly to the API for POST, PUT, and DELETE operations.
- Tests handling of both successful and failed API requests.
- Confirms that success or error messages are displayed as appropriate.

### 3. Importing Commands and Devices

- Verifies that JSON files are correctly parsed and sent to the API.
- Confirms that only valid entries are processed.
- Ensures that the GUI is updated after successful imports.

### 4. Exporting Commands and Devices

- Ensures that commands or devices are written correctly to JSON files.
- Confirms that a success message is displayed after exporting.
- Tests handling of file-related errors.

### 5. Table Refresh and Filtering

- Ensures that search and filter functionality works correctly in the command and device tables.
- Confirms that only the filtered rows are displayed in the GUI.

---

## Notes

- Clipboard copy operations and deletion confirmations are also testable using mocks.
- All tests are designed to be isolated, fast, and repeatable, without relying on actual API calls or filesystem access.

---

## Conclusion

The unit tests verify that `CommandManagerApp` behaves as expected in normal and error scenarios, while using mocks to isolate the application from external dependencies.

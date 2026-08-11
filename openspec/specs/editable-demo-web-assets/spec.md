# editable-demo-web-assets Specification

## Purpose
TBD - created by archiving change extract-demo-web-assets. Update Purpose after archive.
## Requirements
### Requirement: Independently editable demo web assets

The system SHALL store the local demo page markup, styling, and browser event logic in separate HTML, CSS, and JavaScript files outside the Python coordinator module.

#### Scenario: Edit visual styling

- **WHEN** an operator changes the demo stylesheet
- **THEN** the local browser display uses the changed styling on its next page load
- **AND** no Python source edit is required.

### Requirement: Local fixed-asset serving

The local demo server SHALL serve the known demo HTML, CSS, JavaScript, and Babel-fish favicon from loopback-only routes.

#### Scenario: Load the demo display

- **WHEN** a browser opens the local demo URL
- **THEN** it receives the page, stylesheet, script, and favicon from the local server
- **AND** the browser event stream remains available at `/events`.


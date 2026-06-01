# Privacy Policy for speed_core

Last Updated: July 31, 2025

This privacy policy outlines how speed_core handles information. As an open-source project created by a single developer, transparency and user privacy are top priorities.

### Data Collection and Usage

**speed_core does not collect, store, or transmit any personal data or network traffic content.**

The application is designed to be completely self-contained on your computer.

- **Network Monitoring:** The application monitors your network adapters locally to calculate your current upload and download speeds. This information is **only displayed to you** on the widget and is **never sent to any server**.
- **Configuration File:** Your settings are saved locally on your computer in a `speed_core_Config.json` file located in your `%appdata%\speed_core` folder. This file is never transmitted.
- **History Database:** If you use the graph feature, a local SQLite database (`speed_history.db`) is created in the same folder to store your network speed history. This data remains on your computer and is never transmitted.

### Update Checking

To check for new versions, speed_core may periodically contact the GitHub.com API. This is a standard and secure process.

- **Information Sent:** A request is sent to the GitHub API for the speed_core repository to check for new release tags. This request includes basic, non-identifiable information like your IP address, which is standard for any internet connection.
- **No Personal Data:** No personal or user-specific information is sent during the update check.

### Open Source Transparency

speed_core is fully open-source. You are encouraged to review the code on GitHub to verify all claims made in this policy.

### Contact

If you have any questions about this privacy policy, please open an issue on the [GitHub repository](https://github.com/erez-c137/speed_core/issues).

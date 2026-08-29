"""macsetup — declarative provisioner for this Mac.

Makes macOS behave like Windows (keyboard, window management, scrolling)
and installs/configures the tools I use. Every managed setting is a
Component that can report drift (`status`), converge (`apply`), and be
verified (`test`).
"""

__version__ = "1.0.0"

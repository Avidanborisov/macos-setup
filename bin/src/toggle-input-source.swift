// toggle-input-source: Switches to the next enabled keyboard input source.
// Uses the macOS Carbon Input Source API (TISSelectInputSource) directly,
// bypassing symbolic hotkeys for reliable, app-independent switching.
//
// Compile: swiftc -O bin/src/toggle-input-source.swift -o bin/toggle-input-source
// Usage:   bin/toggle-input-source   (no arguments needed)

import Carbon

let sources = TISCreateInputSourceList(nil, false).takeRetainedValue() as! [TISInputSource]
let keyboards = sources.filter { source in
    let category = Unmanaged<CFString>.fromOpaque(
        TISGetInputSourceProperty(source, kTISPropertyInputSourceCategory)
    ).takeUnretainedValue() as String
    let isEnabled = Unmanaged<CFBoolean>.fromOpaque(
        TISGetInputSourceProperty(source, kTISPropertyInputSourceIsEnabled)
    ).takeUnretainedValue()
    return category == (kTISCategoryKeyboardInputSource as String) && CFBooleanGetValue(isEnabled)
}

for source in keyboards {
    let isSelected = Unmanaged<CFBoolean>.fromOpaque(
        TISGetInputSourceProperty(source, kTISPropertyInputSourceIsSelected)
    ).takeUnretainedValue()
    if !CFBooleanGetValue(isSelected) {
        TISSelectInputSource(source)
        break
    }
}

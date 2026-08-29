-- macos-setup: Windows-style Win+Up / Win+Down window behavior.
-- Karabiner turns physical Win+Down/Win+Up into Ctrl+Alt+Down/Up; Hammerspoon
-- owns those two (Rectangle handles the other snapping shortcuts). Being a
-- resident app, it reacts instantly and can remember state:
--   Win+Down: leave fullscreen / restore a maximized window / minimize
--   Win+Up:   un-minimize the most recently Win+Down-minimized window,
--             otherwise maximize (remembering the frame for Win+Down)

hs.window.animationDuration = 0

local savedFrames = {}    -- window id -> frame before we maximized it
local minimizedOrder = {} -- window ids minimized via Win+Down, oldest first

local function isRoughlyMax(win)
    local f, m = win:frame(), win:screen():frame()
    return math.abs(f.x - m.x) <= 2 and math.abs(f.y - m.y) <= 2
        and math.abs(f.w - m.w) <= 4 and math.abs(f.h - m.h) <= 4
end

hs.hotkey.bind({ "ctrl", "alt" }, "down", function()
    local win = hs.window.focusedWindow()
    if not win then return end
    if win:isFullScreen() then
        win:setFullScreen(false)
        return
    end
    if isRoughlyMax(win) then
        local id = win:id()
        local saved = savedFrames[id]
        savedFrames[id] = nil
        if saved then
            win:setFrame(saved)
        else
            -- Maximized before we were watching: restore to 70% centered.
            local m = win:screen():frame()
            win:setFrame({ x = m.x + m.w * 0.15, y = m.y + m.h * 0.15,
                           w = m.w * 0.7, h = m.h * 0.7 })
        end
    else
        table.insert(minimizedOrder, win:id())
        win:minimize()
    end
end)

hs.hotkey.bind({ "ctrl", "alt" }, "up", function()
    -- First bring back the most recently Win+Down-minimized window.
    while #minimizedOrder > 0 do
        local id = table.remove(minimizedOrder)
        local win = hs.window.get(id)
        if win and win:isMinimized() then
            win:unminimize()
            win:focus()
            return
        end
    end
    local win = hs.window.focusedWindow()
    if not win then return end
    if not isRoughlyMax(win) then
        savedFrames[win:id()] = win:frame()
    end
    win:maximize()
end)

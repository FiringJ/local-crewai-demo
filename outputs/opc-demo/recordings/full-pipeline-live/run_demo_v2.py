#!/usr/bin/env python3
"""Navigate OPC demo flow for continuous screen recording (v2)."""
import json
import re
import subprocess
import time

CUA = "/Applications/CuaDriver.app/Contents/MacOS/cua-driver"
PID = 24112
WID = 468


def activate():
    subprocess.run(["osascript", "-e", 'tell application "office-raccoon" to activate'], capture_output=True)
    subprocess.run(
        [
            "osascript",
            "-e",
            'tell application "System Events" to set visible of process "Cursor" to false',
        ],
        capture_output=True,
    )
    subprocess.run(
        [
            "osascript",
            "-e",
            'tell application "System Events" to set visible of process "Cua Driver" to false',
        ],
        capture_output=True,
    )


def call(tool, args=None):
    activate()
    cmd = [CUA, "call", tool, "--compact"]
    if args:
        cmd.append(json.dumps(args))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{tool} failed: {r.stderr or r.stdout}")
    if not r.stdout.strip():
        return {}
    try:
        out = json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"raw": r.stdout}
    return out.get("structuredContent") or out or {}


def pause(secs=2.5):
    time.sleep(secs)


def gw():
    return call("get_window_state", {"pid": PID, "window_id": WID})


def find_index(tree_md, *patterns):
    for pat in patterns:
        for line in tree_md.splitlines():
            if pat in line:
                m = re.search(r"\[(\d+)\]", line)
                if m:
                    return int(m.group(1))
    return None


def click_xy(x, y, wait=1.5):
    call("click", {"pid": PID, "window_id": WID, "x": x, "y": y})
    pause(wait)


def click_el(idx, wait=1.5):
    call("click", {"pid": PID, "window_id": WID, "element_index": idx})
    pause(wait)


def scroll(direction, by="page", amount=2):
    call("scroll", {"pid": PID, "direction": direction, "by": by, "amount": amount})
    pause(1.0)


def ensure_kb():
    state = gw()
    tree = state.get("tree_markdown", "")
    if "contract_audit_rules.md" in tree or "知识库库容" in tree:
        return
    if "云上知识库" not in tree:
        click_xy(95, 175, 1.0)  # expand 数据源
        state = gw()
        tree = state.get("tree_markdown", "")
    kb = find_index(tree, "AXLink (云上知识库)", 'AXStaticText = "云上知识库"')
    if kb:
        click_el(kb, 1.0)
    else:
        click_xy(95, 205, 1.0)


def main():
    call("press_key", {"pid": PID, "window_id": WID, "key": "escape"})
    pause(0.5)

    print("=== Step 1: Knowledge base ===")
    ensure_kb()
    pause(4)

    print("=== Step 2: Scheduled tasks ===")
    state = gw()
    tree = state.get("tree_markdown", "")
    sched = find_index(tree, "AXLink (定时任务)", 'AXStaticText = "定时任务"')
    click_el(sched) if sched else click_xy(95, 250)
    pause(4)

    print("=== Step 3: Run now menu ===")
    state = gw()
    tree = state.get("tree_markdown", "")
    popup = None
    for line in tree.splitlines():
        if "OPC演示-每日" in line and "AXPopUpButton" in line:
            m = re.search(r"\[(\d+)\]", line)
            if m:
                popup = int(m.group(1))
                break
    if popup:
        click_el(popup, 1.0)
    else:
        click_xy(1460, 430, 1.0)
    state = gw()
    tree = state.get("tree_markdown", "")
    run_now = find_index(tree, "立刻运行", "AXMenuItem")
    click_el(run_now, 1.0) if run_now else click_xy(1380, 480, 1.0)
    pause(4)

    print("=== Step 4: History ===")
    state = gw()
    tree = state.get("tree_markdown", "")
    hist = find_index(tree, "AXLink (历史)", 'AXStaticText = "历史"')
    click_el(hist, 1.0) if hist else click_xy(95, 320)
    pause(3)
    click_xy(520, 275, 1.0)
    pause(3)

    print("=== Step 5: Contract session ===")
    state = gw()
    tree = state.get("tree_markdown", "")
    session = find_index(tree, "软件服务合同初审报告")
    click_el(session, 1.0) if session else click_xy(95, 360)
    pause(4)
    scroll("down", "page", 2)
    scroll("up", "page", 2)

    print("=== Step 6: Task planning ===")
    state = gw()
    tree = state.get("tree_markdown", "")
    planning = find_index(tree, 'AXPopUpButton "任务规划"', 'AXMenu "任务规划"')
    click_el(planning, 1.0) if planning else click_xy(485, 875)
    pause(4)

    print("=== Step 7: Scroll to 92% ===")
    scroll("down", "page", 2)
    scroll("up", "page", 3)
    pause(4)

    print("=== Done ===")


if __name__ == "__main__":
    main()

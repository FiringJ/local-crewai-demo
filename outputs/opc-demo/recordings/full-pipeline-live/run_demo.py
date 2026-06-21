#!/usr/bin/env python3
"""Navigate OPC demo flow for continuous screen recording."""
import json
import subprocess
import time
import re

CUA = "/Applications/CuaDriver.app/Contents/MacOS/cua-driver"
PID = 24112
WID = 468


def activate():
    subprocess.run(
        ["osascript", "-e", 'tell application "office-raccoon" to activate'],
        capture_output=True,
    )
    subprocess.run(
        [
            "osascript",
            "-e",
            'tell application "System Events" to set visible of process "Cursor" to false',
        ],
        capture_output=True,
    )


def call(tool, args=None):
    activate()
    cmd = [CUA, "call", tool]
    if args:
        cmd.append(json.dumps(args))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{tool} failed: {r.stderr or r.stdout}")
    try:
        out = json.loads(r.stdout)
        sc = out.get("structuredContent") or {}
        return sc
    except json.JSONDecodeError:
        return {"raw": r.stdout}


def pause(secs=2.0):
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


def click_xy(x, y):
    call("click", {"pid": PID, "window_id": WID, "x": x, "y": y})
    pause(1.5)


def click_el(idx):
    call("click", {"pid": PID, "window_id": WID, "element_index": idx})
    pause(1.5)


def scroll(direction, by="page", amount=2):
    call("scroll", {"pid": PID, "direction": direction, "by": by, "amount": amount})
    pause(1.0)


def ensure_sidebar():
    state = gw()
    tree = state.get("tree_markdown", "")
    if "定时任务" in tree and "云端工作台" in tree:
        return tree
    # Expand sidebar via logo / cloud workbench icon
    click_xy(35, 45)
    pause(1)
    state = gw()
    tree = state.get("tree_markdown", "")
    if "云端工作台" not in tree:
        click_xy(95, 130)
        pause(1)
        state = gw()
        tree = state.get("tree_markdown", "")
    return tree


def main():
    print("=== Step 1: Knowledge base ===")
    tree = ensure_sidebar()
    ds = find_index(tree, 'AXStaticText = "数据源"', "数据源")
    if ds:
        click_el(ds)
    else:
        click_xy(95, 170)
    state = gw()
    tree = state.get("tree_markdown", "")
    kb = find_index(tree, "云上知识库")
    if kb:
        click_el(kb)
    else:
        click_xy(95, 200)
    pause(3)

    print("=== Step 2: Scheduled tasks ===")
    state = gw()
    tree = state.get("tree_markdown", "")
    sched = find_index(tree, "AXLink (定时任务)", 'AXStaticText = "定时任务"')
    if sched:
        click_el(sched)
    else:
        click_xy(95, 230)
    pause(3)

    print("=== Step 3: Run now menu ===")
    state = gw()
    tree = state.get("tree_markdown", "")
    popup = find_index(tree, "OPC演示-每日", "AXPopUpButton")
    if popup:
        click_el(popup)
    else:
        click_xy(1460, 430)
    pause(1)
    state = gw()
    tree = state.get("tree_markdown", "")
    run_now = find_index(tree, "立刻运行", "AXMenuItem")
    if run_now:
        click_el(run_now)
    else:
        click_xy(1380, 480)
    pause(3)

    print("=== Step 4: History ===")
    state = gw()
    tree = state.get("tree_markdown", "")
    hist = find_index(tree, "AXLink (历史)", 'AXStaticText = "历史"')
    if hist:
        click_el(hist)
    else:
        click_xy(95, 285)
    pause(3)
    # Click first history row (daily pipeline run)
    state = gw()
    tree = state.get("tree_markdown", "")
    row = find_index(tree, "OPC演示-每日合同初审流水线")
    if row:
        click_el(row)
    else:
        click_xy(520, 275)
    pause(2)

    print("=== Step 5: Contract session ===")
    state = gw()
    tree = state.get("tree_markdown", "")
    session = find_index(tree, "软件服务合同初审报告")
    if session:
        click_el(session)
    else:
        click_xy(95, 320)
    pause(3)
    scroll("down", "page", 2)
    scroll("up", "page", 2)

    print("=== Step 6: Task planning ===")
    state = gw()
    tree = state.get("tree_markdown", "")
    planning = find_index(tree, 'AXPopUpButton "任务规划"', 'AXMenu "任务规划"')
    if planning:
        click_el(planning)
    else:
        click_xy(485, 875)
    pause(3)

    print("=== Step 7: Scroll to 92% ===")
    scroll("down", "page", 2)
    scroll("up", "page", 3)
    pause(3)

    print("=== Done ===")


if __name__ == "__main__":
    main()

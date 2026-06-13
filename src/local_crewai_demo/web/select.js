const openSelects = new Set();

class CustomSelect {
  constructor(select) {
    this.select = select;
    this.highlightIndex = -1;
    this.build();
    this.bind();
    this.refresh();
  }

  build() {
    const wrapper = document.createElement("div");
    wrapper.className = "cselect";
    this.select.parentNode.insertBefore(wrapper, this.select);
    wrapper.appendChild(this.select);

    this.select.classList.add("cselect__native");
    this.select.tabIndex = -1;
    this.select.setAttribute("aria-hidden", "true");

    this.trigger = document.createElement("button");
    this.trigger.type = "button";
    this.trigger.className = "cselect__trigger";
    this.trigger.setAttribute("aria-haspopup", "listbox");

    this.valueEl = document.createElement("span");
    this.valueEl.className = "cselect__value";

    this.chevron = document.createElement("span");
    this.chevron.className = "cselect__chevron";
    this.chevron.setAttribute("aria-hidden", "true");
    this.chevron.innerHTML =
      '<svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M4 6l4 4 4-4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>';

    this.trigger.append(this.valueEl, this.chevron);

    this.menu = document.createElement("ul");
    this.menu.className = "cselect__menu";
    this.menu.setAttribute("role", "listbox");
    this.menu.hidden = true;

    wrapper.append(this.trigger, this.menu);
    this.wrapper = wrapper;
    this.syncLabel();
  }

  syncLabel() {
    const fieldLabel = this.wrapper.closest("label")?.querySelector(".field__label");
    if (fieldLabel) {
      const labelText = fieldLabel.childNodes[0]?.textContent?.trim();
      if (labelText) {
        this.trigger.setAttribute("aria-label", labelText);
      }
    }
  }

  get options() {
    return [...this.select.options];
  }

  refresh() {
    const selected = this.select.value;
    const selectedOption = this.select.selectedOptions[0];
    this.valueEl.textContent = selectedOption?.textContent?.trim() || "请选择";
    this.menu.innerHTML = "";

    this.options.forEach((option, index) => {
      const item = document.createElement("li");
      const isSelected = option.value === selected;
      item.className = `cselect__option${isSelected ? " is-selected" : ""}`;
      item.setAttribute("role", "option");
      item.setAttribute("aria-selected", String(isSelected));
      item.dataset.value = option.value;
      item.dataset.index = String(index);

      const check = document.createElement("span");
      check.className = "cselect__check";
      check.setAttribute("aria-hidden", "true");
      check.innerHTML =
        '<svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M3.5 8.2 6.4 11 12.5 5" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>';

      const text = document.createElement("span");
      text.className = "cselect__option-text";
      text.textContent = option.textContent?.trim() || option.value;

      item.append(check, text);
      item.addEventListener("click", (event) => {
        event.stopPropagation();
        this.choose(option.value);
      });
      item.addEventListener("mousemove", () => this.setHighlight(index));
      this.menu.appendChild(item);
    });

    if (this.isOpen) {
      this.highlightIndex = Math.max(
        0,
        this.options.findIndex((option) => option.value === selected),
      );
      this.updateHighlight();
    }
  }

  bind() {
    this.trigger.addEventListener("click", (event) => {
      event.stopPropagation();
      this.toggle();
    });

    this.trigger.addEventListener("keydown", (event) => this.onKeydown(event));

    this.select.addEventListener("change", () => this.refresh());
  }

  get isOpen() {
    return this.wrapper.classList.contains("is-open");
  }

  get optionElements() {
    return [...this.menu.querySelectorAll(".cselect__option")];
  }

  toggle() {
    if (this.isOpen) {
      this.close();
    } else {
      this.open();
    }
  }

  open() {
    closeAllSelects(this);
    this.wrapper.classList.add("is-open");
    this.menu.hidden = false;
    this.trigger.setAttribute("aria-expanded", "true");
    this.highlightIndex = Math.max(
      0,
      this.options.findIndex((option) => option.value === this.select.value),
    );
    this.updateHighlight();
    openSelects.add(this);
  }

  close() {
    this.wrapper.classList.remove("is-open");
    this.menu.hidden = true;
    this.trigger.setAttribute("aria-expanded", "false");
    this.highlightIndex = -1;
    openSelects.delete(this);
  }

  choose(value) {
    if (this.select.value !== value) {
      this.select.value = value;
      this.select.dispatchEvent(new Event("change", { bubbles: true }));
    }
    this.refresh();
    this.close();
    this.trigger.focus();
  }

  setHighlight(index) {
    this.highlightIndex = index;
    this.updateHighlight();
  }

  updateHighlight() {
    this.optionElements.forEach((item, index) => {
      item.classList.toggle("is-highlighted", index === this.highlightIndex);
    });
  }

  onKeydown(event) {
    if (event.key === " " || event.key === "Enter") {
      event.preventDefault();
      if (!this.isOpen) {
        this.open();
        return;
      }
      const item = this.optionElements[this.highlightIndex];
      if (item) {
        this.choose(item.dataset.value);
      }
      return;
    }

    if (event.key === "Escape") {
      event.preventDefault();
      this.close();
      return;
    }

    if (event.key === "ArrowDown") {
      event.preventDefault();
      if (!this.isOpen) {
        this.open();
        return;
      }
      this.setHighlight(Math.min(this.highlightIndex + 1, this.optionElements.length - 1));
      this.scrollToHighlighted();
      return;
    }

    if (event.key === "ArrowUp") {
      event.preventDefault();
      if (!this.isOpen) {
        this.open();
        return;
      }
      this.setHighlight(Math.max(this.highlightIndex - 1, 0));
      this.scrollToHighlighted();
    }
  }

  scrollToHighlighted() {
    const item = this.optionElements[this.highlightIndex];
    if (item) {
      item.scrollIntoView({ block: "nearest" });
    }
  }
}

const registry = new WeakMap();

function closeAllSelects(except) {
  openSelects.forEach((instance) => {
    if (instance !== except) {
      instance.close();
    }
  });
}

function initCustomSelects(root = document) {
  root.querySelectorAll(".controls select").forEach((select) => {
    if (!registry.has(select)) {
      registry.set(select, new CustomSelect(select));
      return;
    }
    registry.get(select).refresh();
  });
}

document.addEventListener("click", () => closeAllSelects());
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeAllSelects();
  }
});

window.initCustomSelects = initCustomSelects;

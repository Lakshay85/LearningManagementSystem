import React, { useState, useEffect, useRef, Children, isValidElement } from "react";
import { ChevronDown, Check } from "lucide-react";

/**
 * CustomSelect Component
 * Replaces native <select> with a modern, fully-styled dropdown popup.
 *
 * Supports both:
 * 1. <CustomSelect options={[{ value: 'a', label: 'Option A' }]} value={val} onChange={handleChange} />
 * 2. <CustomSelect value={val} onChange={handleChange}>
 *      <option value="a">Option A</option>
 *    </CustomSelect>
 */
const CustomSelect = ({
  name,
  value,
  onChange,
  options: propOptions,
  children,
  placeholder,
  className = "",
  disabled = false,
  id,
  required = false,
  icon: Icon,
  ...props
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [openUpward, setOpenUpward] = useState(false);
  const containerRef = useRef(null);

  // Normalize options from props or child <option> tags
  const options = React.useMemo(() => {
    if (propOptions && Array.isArray(propOptions)) {
      return propOptions;
    }
    if (children) {
      return Children.toArray(children)
        .map((child) => {
          if (isValidElement(child) && (child.type === "option" || child.props?.value !== undefined)) {
            return {
              value: child.props.value !== undefined ? child.props.value : "",
              label: child.props.children || child.props.label || String(child.props.value),
              disabled: child.props.disabled,
            };
          }
          return null;
        })
        .filter(Boolean);
    }
    return [];
  }, [propOptions, children]);

  // Find currently selected option
  const selectedOption = options.find(
    (opt) => String(opt.value) === String(value)
  );

  const displayLabel = selectedOption
    ? selectedOption.label
    : placeholder || (options.length > 0 ? options[0].label : "Select...");

  // Handle outside clicks to close dropdown
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  // Toggle dropdown and determine direction
  const openMenu = () => {
    if (disabled) return;
    if (containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      const spaceBelow = window.innerHeight - rect.bottom;
      setOpenUpward(spaceBelow < 260 && rect.top > 260);
    }
    setIsOpen(true);
  };

  const toggleOpen = () => {
    if (disabled) return;
    if (!isOpen) {
      openMenu();
    } else {
      setIsOpen(false);
    }
  };

  // Keyboard navigation
  const handleKeyDown = (e) => {
    if (disabled) return;

    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      toggleOpen();
    } else if (e.key === "Escape") {
      setIsOpen(false);
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      if (!isOpen) {
        openMenu();
      } else {
        const currentIndex = options.findIndex(
          (opt) => String(opt.value) === String(value)
        );
        const nextIndex = Math.min(currentIndex + 1, options.length - 1);
        if (options[nextIndex]) {
          handleSelect(options[nextIndex].value);
        }
      }
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      if (!isOpen) {
        openMenu();
      } else {
        const currentIndex = options.findIndex(
          (opt) => String(opt.value) === String(value)
        );
        const prevIndex = Math.max(currentIndex - 1, 0);
        if (options[prevIndex]) {
          handleSelect(options[prevIndex].value);
        }
      }
    }
  };

  const handleSelect = (optionValue) => {
    if (disabled) return;
    setIsOpen(false);

    if (onChange) {
      // Simulate synthetic change event for compatibility with standard form handlers
      onChange({
        target: {
          name: name || id || "",
          value: optionValue,
        },
      });
    }
  };

  return (
    <div
      ref={containerRef}
      className={`relative inline-block w-full text-left ${isOpen ? "z-40" : ""}`}
      {...props}
    >
      {/* Hidden input for HTML form compatibility */}
      <input
        type="hidden"
        name={name}
        value={value ?? ""}
        required={required}
      />

      {/* Dropdown Trigger Button */}
      <button
        type="button"
        id={id}
        disabled={disabled}
        onClick={toggleOpen}
        onKeyDown={handleKeyDown}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        className={`w-full flex items-center justify-between gap-2 px-4 py-2.5 text-sm transition-all duration-200 outline-none select-none cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
        style={{
          background: "var(--theme-card-bg, #ffffff)",
          color: "var(--theme-text-primary, #1e293b)",
          fontFamily: "var(--theme-font-body, inherit)",
        }}
      >
        <div className="flex items-center gap-2 min-w-0 truncate">
          {Icon && <Icon className="w-4 h-4 shrink-0 opacity-60" />}
          <span className="truncate font-medium">{displayLabel}</span>
        </div>
        <ChevronDown
          className={`w-4 h-4 shrink-0 opacity-60 transition-transform duration-200 ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>

      {/* Floating Options Menu */}
      {isOpen && (
        <div
          role="listbox"
          className={`absolute left-0 right-0 z-50 p-1.5 max-h-64 overflow-y-auto shadow-2xl transition-all duration-150 animate-in fade-in zoom-in-95 ${
            openUpward ? "bottom-full mb-1.5" : "top-full mt-1.5"
          }`}
          style={{
            background: "var(--theme-card-bg, #ffffff)",
            border: "var(--theme-card-border, 1px solid #e2e8f0)",
            borderRadius: "var(--theme-card-radius, 1rem)",
            boxShadow:
              "var(--theme-card-shadow, 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1))",
            backdropFilter: "var(--theme-card-backdrop, none)",
            fontFamily: "var(--theme-font-body, inherit)",
          }}
        >
          {options.length === 0 ? (
            <div className="px-4 py-3 text-xs text-center text-gray-400">
              No options available
            </div>
          ) : (
            options.map((opt) => {
              const isSelected = String(opt.value) === String(value);
              return (
                <div
                  key={String(opt.value)}
                  role="option"
                  aria-selected={isSelected}
                  aria-disabled={opt.disabled ? "true" : undefined}
                  title={typeof opt.label === "string" ? opt.label : undefined}
                  onClick={() => !opt.disabled && handleSelect(opt.value)}
                  className={`flex items-center justify-between px-3.5 py-2.5 my-0.5 text-sm rounded-xl cursor-pointer transition-all duration-150 ${
                    opt.disabled ? "opacity-40 cursor-not-allowed" : ""
                  }`}
                  style={{
                    color: "var(--theme-text-primary, #1e293b)",
                    backgroundColor: isSelected
                      ? "var(--theme-accent-light, rgba(16, 185, 129, 0.12))"
                      : "transparent",
                    fontWeight: isSelected ? "600" : "400",
                  }}
                  onMouseEnter={(e) => {
                    if (!opt.disabled && !isSelected) {
                      e.currentTarget.style.backgroundColor =
                        "var(--theme-accent-light, rgba(0, 0, 0, 0.05))";
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!opt.disabled && !isSelected) {
                      e.currentTarget.style.backgroundColor = "transparent";
                    }
                  }}
                >
                  <span className="truncate">{opt.label}</span>
                  {isSelected && (
                    <Check
                      className="w-4 h-4 shrink-0 ml-2"
                      style={{ color: "var(--theme-accent, #10b981)" }}
                    />
                  )}
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
};

export default CustomSelect;

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
  size = "md", // "sm" | "md" | "lg"
  menuClassName = "",
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

  // Detect custom styling passed in className
  const hasCustomBg = className.includes("bg-");
  const hasCustomText = className.includes("text-");
  const hasCustomPadding = className.includes("py-") || className.includes("px-");

  const sizeClasses =
    size === "sm"
      ? "px-2.5 py-1 text-xs rounded-lg"
      : size === "lg"
      ? "px-4 py-3 text-base rounded-2xl"
      : "px-3.5 py-2 text-xs rounded-xl";

  return (
    <div
      ref={containerRef}
      className={`relative inline-block w-full text-left ${isOpen ? "z-50" : ""}`}
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
        className={`w-full flex items-center justify-between gap-2 border border-slate-200 transition-all duration-150 outline-none select-none cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed ${
          !hasCustomPadding ? sizeClasses : ""
        } ${className} ${isOpen ? "ring-2 ring-indigo-500/20 border-indigo-500" : ""}`}
        style={{
          ...(!hasCustomBg ? { background: "var(--theme-card-bg, #ffffff)", backgroundColor: "#ffffff" } : {}),
          ...(!hasCustomText ? { color: "var(--theme-text-primary, #1e293b)" } : {}),
          fontFamily: "var(--theme-font-body, inherit)",
        }}
      >
        <div className="flex items-center gap-2 min-w-0 truncate">
          {Icon && <Icon className="w-4 h-4 shrink-0 opacity-60" />}
          <span className="truncate font-medium">{displayLabel}</span>
        </div>
        <ChevronDown
          className={`w-3.5 h-3.5 shrink-0 opacity-60 transition-transform duration-200 ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>

      {/* Floating Options Menu */}
      {isOpen && (
        <div
          role="listbox"
          className={`absolute left-0 z-[100] min-w-full w-max max-w-xs p-1 max-h-60 overflow-y-auto shadow-xl rounded-xl border border-slate-200 bg-white transition-all duration-150 ${
            openUpward ? "bottom-full mb-1.5" : "top-full mt-1.5"
          } ${menuClassName}`}
          style={{
            backgroundColor: "#ffffff",
            background: "#ffffff",
            boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.12), 0 8px 10px -6px rgba(0, 0, 0, 0.08)",
          }}
        >
          {options.length === 0 ? (
            <div className="px-3 py-2 text-xs text-center text-slate-400">
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
                  className={`flex items-center justify-between px-3 py-2 my-0.5 text-xs rounded-lg cursor-pointer transition-colors duration-100 ${
                    opt.disabled
                      ? "opacity-40 cursor-not-allowed text-slate-300"
                      : isSelected
                      ? "bg-indigo-50 text-indigo-700 font-semibold"
                      : "text-slate-800 hover:bg-slate-100 font-medium"
                  }`}
                >
                  <span className="truncate">{opt.label}</span>
                  {isSelected && (
                    <Check
                      className="w-3.5 h-3.5 shrink-0 ml-2 text-indigo-600"
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

import { useRef, useState } from "react";

import { cn } from "@/lib/utils";

type FileDropzoneProps = {
  file: File | null;
  onFileChange: (file: File | null) => void;
};

function DocumentIcon() {
  return (
    <svg className="size-[26px]" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M9 5.5h9.2L21 8.3V24.5a1.5 1.5 0 0 1-1.5 1.5H9a1.5 1.5 0 0 1-1.5-1.5V7a1.5 1.5 0 0 1 1.5-1.5Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <path d="M18.2 5.5V8.3H21" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
      <path
        d="M11 12.5h8M11 15.5h6.5M11 18.5h7.5"
        stroke="currentColor"
        strokeWidth="1.25"
        strokeLinecap="round"
        opacity="0.42"
      />
      <circle
        cx="23"
        cy="23"
        r="5.5"
        fill="currentColor"
        fillOpacity="0.12"
        stroke="currentColor"
        strokeWidth="1.25"
      />
      <path
        d="M23 20.8v4.4M21.3 22.5h3.4"
        stroke="currentColor"
        strokeWidth="1.35"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function FileDropzone({ file, onFileChange }: FileDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  const handleFiles = (files: FileList | null) => {
    onFileChange(files?.[0] ?? null);
  };

  return (
    <div
      className={cn(
        "dropzone",
        dragOver && "dropzone--drag",
        file && "dropzone--has-file",
      )}
      onDragOver={(event) => {
        event.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(event) => {
        event.preventDefault();
        setDragOver(false);
        handleFiles(event.dataTransfer.files);
      }}
      onClick={() => inputRef.current?.click()}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          inputRef.current?.click();
        }
      }}
      role="button"
      tabIndex={0}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.docx,.docm,.txt,.md,.csv"
        className="sr-only"
        onChange={(event) => handleFiles(event.target.files)}
      />

      <div className="dropzone__body">
        <span className="dropzone__icon">
          <DocumentIcon />
        </span>
        <p className="dropzone__hint">拖放文件，或点击选择</p>
        <p className="dropzone__formats">PDF · DOCX · TXT · MD · CSV</p>
        {file ? <span className="dropzone__filename">{file.name}</span> : null}
      </div>
    </div>
  );
}

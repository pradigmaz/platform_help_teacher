'use client';

import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Upload } from 'lucide-react';
import { cn } from '@/lib/utils';

interface DropzoneProps {
  onFileDrop: (file: File) => void;
  isUploading?: boolean;
  accept?: string;
  className?: string;
}

export function Dropzone({ onFileDrop, isUploading, accept, className }: DropzoneProps) {
  const [isDragActive, setIsDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    const file = e.dataTransfer.files?.[0];
    if (file) {
      onFileDrop(file);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onFileDrop(file);
    }
  };

  return (
    <div
      className={cn(
        "relative group cursor-pointer",
        className
      )}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
    >
      <input
        type="file"
        ref={inputRef}
        className="hidden"
        accept={accept}
        onChange={handleFileChange}
      />
      
      <motion.div
        animate={{
          scale: isDragActive ? 1.01 : 1,
          borderColor: isDragActive ? "hsl(var(--primary))" : "hsl(var(--border))",
          backgroundColor: isDragActive ? "hsla(var(--primary) / 0.05)" : "transparent",
        }}
        className={cn(
          "flex flex-col items-center justify-center gap-4 p-10 border-2 border-dashed rounded-2xl transition-colors duration-200",
          isDragActive ? "border-primary" : "hover:bg-accent/50 hover:border-primary/50"
        )}
      >
        <div className="relative">
          <motion.div
            animate={{
              y: isDragActive ? -8 : 0,
            }}
            transition={{
              type: "spring",
              stiffness: 300,
              damping: 20
            }}
          >
            <Upload className={cn(
              "w-10 h-10 transition-colors duration-200",
              isDragActive ? "text-primary" : "text-muted-foreground group-hover:text-primary"
            )} />
          </motion.div>
          
          <AnimatePresence>
            {isDragActive && (
              <motion.div
                initial={{ opacity: 0, scale: 0.5 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.5 }}
                className="absolute -top-1 -right-1 w-3 h-3 bg-primary rounded-full"
              />
            )}
          </AnimatePresence>
        </div>

        <div className="text-center">
          <p className="text-base font-medium text-foreground">
            {isUploading ? "Загрузка..." : "Перетащите файл сюда или нажмите для выбора"}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            {accept?.includes('image') 
              ? 'Поддерживаются JPG, PNG, GIF, WebP'
              : 'Поддерживаются .xlsx, .docx, .txt, .csv'
            }
          </p>
        </div>
      </motion.div>
    </div>
  );
}

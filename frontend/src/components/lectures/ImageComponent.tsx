'use client';

import { useCallback, useState, useRef, useEffect } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { $getNodeByKey, type NodeKey } from 'lexical';
import { motion } from 'motion/react';
import { 
  ImageIcon, 
  Trash2, 
  Maximize2, 
  GripVertical,
  AlignLeft,
  AlignCenter,
  AlignRight
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { 
  Popover, 
  PopoverContent, 
  PopoverTrigger 
} from '@/components/ui/popover';
import { Dropzone } from '@/components/animate-ui/dropzone';
import { cn } from '@/lib/utils';
import { $isImageNode, type ImageDimension } from './nodes/ImageNode';

interface ImageComponentProps {
  nodeKey: NodeKey;
  src: string;
  altText: string;
  caption: string;
  width: ImageDimension;
  height: ImageDimension;
}

type Alignment = 'left' | 'center' | 'right';

export function ImageComponent({
  nodeKey,
  src,
  altText,
  caption,
  width,
  height,
}: ImageComponentProps) {
  const [editor] = useLexicalComposerContext();
  const [isSelected, setIsSelected] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  const [localCaption, setLocalCaption] = useState(caption);
  const [alignment, setAlignment] = useState<Alignment>('center');
  const [isUploading, setIsUploading] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);


  // Sync caption with node
  useEffect(() => {
    setLocalCaption(caption);
  }, [caption]);

  const updateCaption = useCallback((newCaption: string) => {
    setLocalCaption(newCaption);
    editor.update(() => {
      const node = $getNodeByKey(nodeKey);
      if ($isImageNode(node)) {
        node.setCaption(newCaption);
      }
    });
  }, [editor, nodeKey]);

  const updateDimensions = useCallback((newWidth: ImageDimension, newHeight: ImageDimension) => {
    editor.update(() => {
      const node = $getNodeByKey(nodeKey);
      if ($isImageNode(node)) {
        node.setDimensions(newWidth, newHeight);
      }
    });
  }, [editor, nodeKey]);

  const updateSrc = useCallback((newSrc: string) => {
    editor.update(() => {
      const node = $getNodeByKey(nodeKey);
      if ($isImageNode(node)) {
        node.setSrc(newSrc);
      }
    });
  }, [editor, nodeKey]);

  const deleteNode = useCallback(() => {
    editor.update(() => {
      const node = $getNodeByKey(nodeKey);
      if (node) {
        node.remove();
      }
    });
  }, [editor, nodeKey]);

  const handleFileDrop = useCallback(async (file: File) => {
    if (!file.type.startsWith('image/')) {
      return;
    }
    
    setIsUploading(true);
    
    // Create local preview first
    const reader = new FileReader();
    reader.onload = (e) => {
      const dataUrl = e.target?.result as string;
      updateSrc(dataUrl);
      setIsUploading(false);
    };
    reader.readAsDataURL(file);
    
    // TODO: Upload to server and replace with real URL
    // const formData = new FormData();
    // formData.append('file', file);
    // const response = await api.post('/lectures/images', formData);
    // updateSrc(response.data.url);
  }, [updateSrc]);

  // Resize handling
  const handleResizeStart = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsResizing(true);
    
    const startX = e.clientX;
    const startWidth = imageRef.current?.offsetWidth || 400;
    
    const handleMouseMove = (moveEvent: MouseEvent) => {
      const deltaX = moveEvent.clientX - startX;
      const newWidth = Math.max(100, Math.min(800, startWidth + deltaX));
      updateDimensions(newWidth, 'auto');
    };
    
    const handleMouseUp = () => {
      setIsResizing(false);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
    
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  }, [updateDimensions]);

  const alignmentClasses: Record<Alignment, string> = {
    left: 'mr-auto',
    center: 'mx-auto',
    right: 'ml-auto',
  };

  // No image yet - show dropzone
  if (!src) {
    return (
      <div className="my-4">
        <Dropzone
          onFileDrop={handleFileDrop}
          isUploading={isUploading}
          accept="image/*"
          className="max-w-md mx-auto"
        />
      </div>
    );
  }


  return (
    <div 
      ref={containerRef}
      className={cn(
        "my-4 group relative",
        isSelected && "ring-2 ring-primary ring-offset-2 rounded-lg"
      )}
      onClick={() => setIsSelected(true)}
      onBlur={() => setIsSelected(false)}
      tabIndex={0}
    >
      <motion.figure
        className={cn("relative", alignmentClasses[alignment])}
        style={{ 
          width: width === 'auto' ? 'fit-content' : width,
          maxWidth: '100%'
        }}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
      >
        {/* Image */}
        <div className="relative overflow-hidden rounded-lg">
          <img
            ref={imageRef}
            src={src}
            alt={altText}
            className={cn(
              "block max-w-full h-auto rounded-lg",
              isResizing && "pointer-events-none select-none"
            )}
            style={{
              width: width === 'auto' ? 'auto' : `${width}px`,
              height: height === 'auto' ? 'auto' : `${height}px`,
            }}
            draggable={false}
          />
          
          {/* Resize handle */}
          <div
            className={cn(
              "absolute right-0 top-0 bottom-0 w-3 cursor-ew-resize",
              "opacity-0 group-hover:opacity-100 transition-opacity",
              "flex items-center justify-center"
            )}
            onMouseDown={handleResizeStart}
          >
            <div className="h-8 w-1 bg-primary/50 rounded-full" />
          </div>
        </div>

        {/* Caption */}
        <figcaption className="mt-2">
          <Input
            value={localCaption}
            onChange={(e) => updateCaption(e.target.value)}
            placeholder="Добавить подпись..."
            className="text-center text-sm text-muted-foreground border-none bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0"
          />
        </figcaption>

        {/* Toolbar (visible on hover/select) */}
        <div className={cn(
          "absolute -top-10 left-1/2 -translate-x-1/2",
          "flex items-center gap-1 p-1 rounded-lg",
          "bg-background/95 backdrop-blur border shadow-lg",
          "opacity-0 group-hover:opacity-100 transition-opacity",
          isSelected && "opacity-100"
        )}>
          {/* Alignment buttons */}
          <Button
            variant={alignment === 'left' ? 'secondary' : 'ghost'}
            size="sm"
            className="h-7 w-7 p-0"
            onClick={() => setAlignment('left')}
          >
            <AlignLeft className="h-3.5 w-3.5" />
          </Button>
          <Button
            variant={alignment === 'center' ? 'secondary' : 'ghost'}
            size="sm"
            className="h-7 w-7 p-0"
            onClick={() => setAlignment('center')}
          >
            <AlignCenter className="h-3.5 w-3.5" />
          </Button>
          <Button
            variant={alignment === 'right' ? 'secondary' : 'ghost'}
            size="sm"
            className="h-7 w-7 p-0"
            onClick={() => setAlignment('right')}
          >
            <AlignRight className="h-3.5 w-3.5" />
          </Button>
          
          <div className="w-px h-4 bg-border mx-1" />
          
          {/* Replace image */}
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                <ImageIcon className="h-3.5 w-3.5" />
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-64 p-2">
              <Dropzone
                onFileDrop={handleFileDrop}
                isUploading={isUploading}
                accept="image/*"
              />
            </PopoverContent>
          </Popover>
          
          {/* Delete */}
          <Button
            variant="ghost"
            size="sm"
            className="h-7 w-7 p-0 text-destructive hover:text-destructive"
            onClick={deleteNode}
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      </motion.figure>
    </div>
  );
}

export default ImageComponent;

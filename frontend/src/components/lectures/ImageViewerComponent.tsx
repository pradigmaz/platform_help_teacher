'use client';

import { motion } from 'motion/react';
import { cn } from '@/lib/utils';
import type { ImageDimension } from './nodes/ImageNode';

interface ImageViewerComponentProps {
  src: string;
  altText: string;
  caption: string;
  width: ImageDimension;
  height: ImageDimension;
}

export function ImageViewerComponent({
  src,
  altText,
  caption,
  width,
  height,
}: ImageViewerComponentProps) {
  if (!src) {
    return null;
  }

  return (
    <motion.figure
      className="my-6 mx-auto"
      style={{ 
        width: width === 'auto' ? 'fit-content' : width,
        maxWidth: '100%'
      }}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className="overflow-hidden rounded-lg">
        <img
          src={src}
          alt={altText}
          className="block max-w-full h-auto rounded-lg"
          style={{
            width: width === 'auto' ? 'auto' : `${width}px`,
            height: height === 'auto' ? 'auto' : `${height}px`,
          }}
          loading="lazy"
        />
      </div>
      
      {caption && (
        <figcaption className="mt-2 text-center text-sm text-muted-foreground">
          {caption}
        </figcaption>
      )}
    </motion.figure>
  );
}

export default ImageViewerComponent;

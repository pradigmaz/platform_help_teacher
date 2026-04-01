'use client';

import Image from 'next/image';
import { motion } from 'motion/react';
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
        <Image
          src={src}
          alt={altText}
          width={width === 'auto' ? 500 : Number(width)}
          height={height === 'auto' ? 300 : Number(height)}
          className="block max-w-full h-auto rounded-lg"
          style={{
            width: width === 'auto' ? 'auto' : `${width}px`,
            height: height === 'auto' ? 'auto' : `${height}px`,
          }}
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

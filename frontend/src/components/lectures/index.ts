// Lecture editor components
export { CodeBlockComponent } from './CodeBlockComponent';
export { ImageComponent } from './ImageComponent';
export { VisualizationSandbox } from './VisualizationSandbox';
export { EditorToolbar } from './EditorToolbar';
export { LectureEditor } from './LectureEditor';

// Lecture viewer components (read-only)
export { LectureViewer } from './LectureViewer';
export { CodeBlockViewerComponent } from './CodeBlockViewerComponent';
export { ImageViewerComponent } from './ImageViewerComponent';

// Lexical nodes (Editor)
export { 
  CodeBlockNode, 
  $createCodeBlockNode, 
  $isCodeBlockNode,
  type CodeLanguage,
  type RenderMode,
  type SerializedCodeBlockNode,
} from './nodes/CodeBlockNode';

export { 
  ImageNode, 
  $createImageNode, 
  $isImageNode,
  type ImageDimension,
  type SerializedImageNode,
} from './nodes/ImageNode';

// Lexical nodes (Viewer)
export { ViewerCodeBlockNode } from './nodes/ViewerCodeBlockNode';
export { ViewerImageNode } from './nodes/ViewerImageNode';

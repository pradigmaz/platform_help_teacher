'use client';

import { useEffect } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { $insertNodeToNearestRoot } from '@lexical/utils';
import { COMMAND_PRIORITY_EDITOR } from 'lexical';
import {
  INSERT_HORIZONTAL_RULE_COMMAND,
  $createHorizontalRuleNode,
  HorizontalRuleNode,
} from '../nodes/HorizontalRuleNode';

export function HorizontalRulePlugin(): null {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    if (!editor.hasNodes([HorizontalRuleNode])) {
      throw new Error('HorizontalRulePlugin: HorizontalRuleNode not registered on editor');
    }

    return editor.registerCommand(
      INSERT_HORIZONTAL_RULE_COMMAND,
      () => {
        const hrNode = $createHorizontalRuleNode();
        $insertNodeToNearestRoot(hrNode);
        return true;
      },
      COMMAND_PRIORITY_EDITOR
    );
  }, [editor]);

  return null;
}

export default HorizontalRulePlugin;

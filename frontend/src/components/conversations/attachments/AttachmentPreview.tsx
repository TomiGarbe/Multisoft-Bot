import { memo } from 'react';
import type { Attachment } from '@/types/chat';
import AudioAttachment from './AudioAttachment';
import DocumentAttachment from './DocumentAttachment';
import ImageAttachment from './ImageAttachment';
import ProcessingArtifact from './ProcessingArtifact';
import VideoAttachment from './VideoAttachment';

function AttachmentPreviewBase({ attachment }: { attachment: Attachment }) {
  console.warn('[MESSAGE_ATTACHMENT]', {
    attachmentId: attachment.id,
    messageId: attachment.messageId,
    type: attachment.type,
    status: attachment.status,
    mimeType: attachment.mimeType,
    hasStream: Boolean(attachment.streamUrl),
  });
  return (
    <div className="flex flex-col gap-1.5">
      {attachment.type === 'image' ? <ImageAttachment attachment={attachment} /> : null}
      {attachment.type === 'audio' ? <AudioAttachment attachment={attachment} /> : null}
      {attachment.type === 'video' ? <VideoAttachment attachment={attachment} /> : null}
      {(attachment.type === 'document' || attachment.type === 'file') ? <DocumentAttachment attachment={attachment} /> : null}
      {attachment.type !== 'audio' ? <ProcessingArtifact attachment={attachment} /> : null}
    </div>
  );
}

const AttachmentPreview = memo(AttachmentPreviewBase);
export default AttachmentPreview;

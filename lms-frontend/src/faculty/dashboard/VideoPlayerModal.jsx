import React, { useEffect } from "react";
import { X } from "lucide-react";

const VideoPlayerModal = ({ videoUrl, title, onClose }) => {
    // Close on escape key
    useEffect(() => {
        const handleEsc = (e) => {
            if (e.key === "Escape") onClose();
        };
        window.addEventListener("keydown", handleEsc);
        return () => window.removeEventListener("keydown", handleEsc);
    }, [onClose]);

    if (!videoUrl) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="relative w-full max-w-5xl bg-black rounded-2xl overflow-hidden shadow-2xl ring-1 ring-white/10 animate-in zoom-in-95 duration-200">
                {/* Header */}
                <div className="absolute top-0 left-0 right-0 z-10 flex items-center justify-between p-4 bg-gradient-to-b from-black/80 to-transparent">
                    <h3 className="text-white font-medium text-lg drop-shadow-md truncate pr-8">
                        {title}
                    </h3>
                    <button
                        onClick={onClose}
                        className="p-2 text-white/80 hover:text-white bg-black/40 hover:bg-black/60 rounded-full backdrop-blur-md transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Video Player */}
                <div className="aspect-video w-full bg-black flex items-center justify-center">
                    <video
                        src={videoUrl}
                        controls
                        autoPlay
                        className="w-full h-full object-contain"
                        controlsList="nodownload"
                    >
                        Your browser does not support the video tag.
                    </video>
                </div>
            </div>

            {/* Backdrop click handler */}
            <div className="absolute inset-0 -z-10" onClick={onClose} />
        </div>
    );
};

export default VideoPlayerModal;

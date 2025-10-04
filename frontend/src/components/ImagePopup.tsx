import React, { useRef, useState, useEffect } from "react";
import "./ImagePopup.css";

interface ImagePopupProps {
	files: File[];
	open: boolean;
	onClose: () => void;
	anchorRight?: boolean; // If true, hug right wall
}

const MIN_WIDTH = 400;
const MIN_HEIGHT = 300;

const ImagePopup: React.FC<ImagePopupProps> = ({
	files,
	open,
	onClose,
	anchorRight = true,
}) => {
	// Reset state on mount (key change)
	const [position, setPosition] = useState<{ x: number; y: number }>({
		x: 0,
		y: 0,
	});
	const [size, setSize] = useState<{ width: number; height: number }>({
		width: 600,
		height: 600,
	});
	const [dragging, setDragging] = useState(false);
	const [resizing, setResizing] = useState(false);
	const [dragOffset, setDragOffset] = useState<{ x: number; y: number }>({
		x: 0,
		y: 0,
	});
	const [zoom, setZoom] = useState(1); // 1 = 100%
	const [rotation, setRotation] = useState(0); // degrees
	const [activeTabIndex, setActiveTabIndex] = useState(0); // Track active tab
	// Rotate image 90deg clockwise
	const handleRotate = () => setRotation((r) => (r + 90) % 360);
	const popupRef = useRef<HTMLDivElement>(null);
	const imgRef = useRef<HTMLImageElement>(null);

	// Reset all state when remounted (key changes)
	useEffect(() => {
		setPosition({ x: 0, y: 0 });
		setSize({ width: 600, height: 600 });
		setZoom(1);
		setActiveTabIndex(0);
	}, []);

	// Reset active tab when files change
	useEffect(() => {
		if (files.length > 0 && activeTabIndex >= files.length) {
			setActiveTabIndex(0);
		}
	}, [files, activeTabIndex]);

	// Hug right wall only on initial open
	useEffect(() => {
		if (open && anchorRight && popupRef.current) {
			// Only set position if just opened
			setPosition((prev) => {
				// If already moved, don't reset
				if (prev.x !== 0 || prev.y !== 0) return prev;
				const winW = window.innerWidth;
				return {
					x: winW - size.width - 24, // 24px margin
					y: 24,
				};
			});
		}
		// eslint-disable-next-line
	}, [open, anchorRight]);

	// Drag logic
	const onDragStart = (e: React.MouseEvent) => {
		setDragging(true);
		setDragOffset({
			x: e.clientX - position.x,
			y: e.clientY - position.y,
		});
		document.body.style.userSelect = "none";
	};
	const onDrag = (e: MouseEvent) => {
		if (dragging) {
			setPosition({
				x: e.clientX - dragOffset.x,
				y: e.clientY - dragOffset.y,
			});
		}
	};
	const onDragEnd = () => {
		setDragging(false);
		document.body.style.userSelect = "";
	};

	// Resize logic
	const onResizeStart = (e: React.MouseEvent) => {
		setResizing(true);
		setDragOffset({
			x: e.clientX,
			y: e.clientY,
		});
		document.body.style.userSelect = "none";
	};
	const onResize = (e: MouseEvent) => {
		if (resizing && popupRef.current) {
			const dx = e.clientX - dragOffset.x;
			const dy = e.clientY - dragOffset.y;
			setSize((prev) => ({
				width: Math.max(MIN_WIDTH, prev.width + dx),
				height: Math.max(MIN_HEIGHT, prev.height + dy),
			}));
			setDragOffset({ x: e.clientX, y: e.clientY });
		}
	};
	const onResizeEnd = () => {
		setResizing(false);
		document.body.style.userSelect = "";
	};

	useEffect(() => {
		if (dragging) {
			window.addEventListener("mousemove", onDrag);
			window.addEventListener("mouseup", onDragEnd);
			return () => {
				window.removeEventListener("mousemove", onDrag);
				window.removeEventListener("mouseup", onDragEnd);
			};
		}
		if (resizing) {
			window.addEventListener("mousemove", onResize);
			window.addEventListener("mouseup", onResizeEnd);
			return () => {
				window.removeEventListener("mousemove", onResize);
				window.removeEventListener("mouseup", onResizeEnd);
			};
		}
	}, [dragging, resizing, dragOffset]);

	// Zoom controls
	const handleZoomIn = () => setZoom((z) => Math.min(z + 0.1, 3));
	const handleZoomOut = () => setZoom((z) => Math.max(z - 0.1, 0.1));
	const handleResetZoom = () => setZoom(1);

	if (!open || files.length === 0) return null;

	const currentFile = files[activeTabIndex];

	return (
		<div
			ref={popupRef}
			className="image-popup"
			style={{
				position: "fixed",
				left: position.x,
				top: position.y,
				width: size.width,
				height: size.height,
				zIndex: 1000,
			}}
		>
			{/* Header with drag handle and controls */}
			<div className="image-popup-header" onMouseDown={onDragStart}>
				<span className="drag-handle">☰</span>
				<span className="title">
					{files.length > 1
						? `Image ${activeTabIndex + 1} of ${files.length}`
						: "Original Image"}
				</span>
				{/* Zoom and rotate controls */}
				<div className="controls">
					<button
						onClick={handleZoomOut}
						className="control-btn zoom-btn"
						title="Zoom Out"
					>
						-
					</button>
					<span className="zoom-display">{Math.round(zoom * 100)}%</span>
					<button
						onClick={handleZoomIn}
						className="control-btn zoom-btn"
						title="Zoom In"
					>
						+
					</button>
					<button
						onClick={handleResetZoom}
						className="control-btn reset-btn"
						title="Reset Zoom"
					>
						100%
					</button>
					<button
						onClick={handleRotate}
						className="control-btn rotate-btn"
						title="Rotate 90°"
					>
						↷
					</button>
					<button
						onClick={onClose}
						className="control-btn close-btn"
						title="Close"
					>
						✕
					</button>
				</div>
			</div>

			{/* Main content area with tabs and image */}
			<div className="popup-main-content">
				{/* Vertical Manila folder tabs */}
				{files.length > 1 && (
					<div className="manila-tabs-container">
						<div className="manila-tabs-scroll">
							{files.slice(0, 50).map((file, index) => {
								// Use consistent tab height for better scrolling experience
								const tabHeight = 24; // Fixed height for consistent appearance
								const tabSpacing = 2; // Small gap between tabs

								return (
									<div
										key={`${file.name}-${index}`}
										className={`manila-tab ${
											index === activeTabIndex ? "active" : ""
										}`}
										style={{
											zIndex:
												index === activeTabIndex ? 100 : 99 - (index % 50),
											height: `${tabHeight}px`,
											marginBottom: `${tabSpacing}px`,
										}}
										onClick={() => {
											setActiveTabIndex(index);
											// Reset zoom and rotation when switching tabs
											setZoom(1);
											setRotation(0);
										}}
										title={file.name}
									>
										<span className="manila-tab-number">{index + 1}</span>
									</div>
								);
							})}
							{files.length > 50 && (
								<div className="manila-tab-overflow">+{files.length - 50}</div>
							)}
						</div>
					</div>
				)}
				{/* Image area with scroll */}
				<div className="image-container">
					<div className="image-wrapper">
						<img
							ref={imgRef}
							src={URL.createObjectURL(currentFile)}
							alt={`Document ${activeTabIndex + 1}`}
							className="popup-image"
							style={{
								transform: `scale(${zoom}) rotate(${rotation}deg)`,
								transformOrigin: "center",
							}}
						/>
					</div>
				</div>
			</div>
			{/* Resize handle */}
			<div onMouseDown={onResizeStart} className="resize-handle" title="Resize">
				<svg width="20" height="20">
					<polyline points="0,20 20,0" stroke="#1976d2" strokeWidth="2" />
				</svg>
			</div>
		</div>
	);
};

export default ImagePopup;

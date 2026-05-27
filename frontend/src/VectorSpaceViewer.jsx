import React, { useRef, useState, Suspense } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Html, Line } from "@react-three/drei";
import * as THREE from "three";

// ─── Colour helper: maps 0–1 value to a viridis-inspired gradient ──────────
function valueToColor(t) {
  // Deep purple → teal → yellow
  const r = Math.round(68  + t * (253 - 68));
  const g = Math.round(1   + t * (231 - 1));
  const b = Math.round(84  + t * (37  - 84));
  return `rgb(${r},${g},${b})`;
}

// ─── Single animated sphere point ──────────────────────────────────────────
function DataPoint({ position, color, label, document, isHovered, onHover, onUnhover }) {
  const meshRef = useRef();
  const targetScale = isHovered ? 2.0 : 1.0;

  useFrame(() => {
    if (meshRef.current) {
      meshRef.current.scale.lerp(
        new THREE.Vector3(targetScale, targetScale, targetScale),
        0.12
      );
    }
  });

  return (
    <mesh
      ref={meshRef}
      position={position}
      onPointerEnter={(e) => { e.stopPropagation(); onHover(); }}
      onPointerLeave={() => onUnhover()}
    >
      <sphereGeometry args={[0.09, 16, 16]} />
      <meshStandardMaterial
        color={color}
        emissive={color}
        emissiveIntensity={isHovered ? 0.8 : 0.25}
        roughness={0.3}
        metalness={0.1}
      />
      {isHovered && (
        <Html distanceFactor={8} style={{ pointerEvents: "none" }}>
          <div style={{
            background: "rgba(17, 15, 18, 0.92)",
            border: "1px solid rgba(245, 158, 11, 0.5)",
            borderRadius: "8px",
            padding: "0.6rem 0.85rem",
            minWidth: "180px",
            maxWidth: "240px",
            backdropFilter: "blur(12px)",
            boxShadow: "0 8px 24px rgba(0,0,0,0.5)",
            pointerEvents: "none",
          }}>
            <p style={{
              fontFamily: "JetBrains Mono, monospace",
              fontSize: "0.72rem",
              color: "#f59e0b",
              margin: "0 0 0.3rem 0",
              fontWeight: 600,
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap"
            }}>
              {label}
            </p>
            <p style={{
              fontSize: "0.75rem",
              color: "#beb6a7",
              margin: 0,
              lineHeight: 1.5,
              display: "-webkit-box",
              WebkitLineClamp: 3,
              WebkitBoxOrient: "vertical",
              overflow: "hidden",
            }}>
              {document || "—"}
            </p>
          </div>
        </Html>
      )}
    </mesh>
  );
}

// ─── XYZ Axis lines ─────────────────────────────────────────────────────────
function AxisLines({ size = 3 }) {
  return (
    <>
      <Line points={[[-size, 0, 0], [size, 0, 0]]} color="#ef4444" lineWidth={1} opacity={0.4} transparent />
      <Line points={[[0, -size, 0], [0, size, 0]]} color="#22c55e" lineWidth={1} opacity={0.4} transparent />
      <Line points={[[0, 0, -size], [0, 0, size]]} color="#3b82f6" lineWidth={1} opacity={0.4} transparent />
    </>
  );
}

// ─── The Three.js scene ──────────────────────────────────────────────────────
function Scene({ points }) {
  const [hovered, setHovered] = useState(null);

  // Normalise coordinates to fit in [-3, 3] range
  const xs = points.map(p => p.x);
  const ys = points.map(p => p.y);
  const zs = points.map(p => p.z);
  const minX = Math.min(...xs), maxX = Math.max(...xs);
  const minY = Math.min(...ys), maxY = Math.max(...ys);
  const minZ = Math.min(...zs), maxZ = Math.max(...zs);
  const rangeX = maxX - minX || 1;
  const rangeY = maxY - minY || 1;
  const rangeZ = maxZ - minZ || 1;

  const normalised = points.map((p, i) => {
    const nx = ((p.x - minX) / rangeX - 0.5) * 6;
    const ny = ((p.y - minY) / rangeY - 0.5) * 6;
    const nz = ((p.z - minZ) / rangeZ - 0.5) * 6;
    const t  = i / Math.max(points.length - 1, 1); // colour gradient index
    return { ...p, nx, ny, nz, color: valueToColor(t) };
  });

  return (
    <>
      <ambientLight intensity={0.6} />
      <pointLight position={[10, 10, 10]} intensity={1.2} />
      <pointLight position={[-10, -10, -10]} intensity={0.4} color="#f59e0b" />
      <OrbitControls enableDamping dampingFactor={0.08} />
      <AxisLines />
      {normalised.map((p, i) => (
        <DataPoint
          key={p.id}
          position={[p.nx, p.ny, p.nz]}
          color={p.color}
          label={p.id}
          document={p.document}
          isHovered={hovered === i}
          onHover={() => setHovered(i)}
          onUnhover={() => setHovered(null)}
        />
      ))}
    </>
  );
}

// ─── Public component ────────────────────────────────────────────────────────
export default function VectorSpaceViewer({
  vizData,
  isLoading,
  vizMethod,
  onMethodChange,
  onRefresh,
}) {
  // ── Empty / loading states ──
  if (isLoading) {
    return (
      <div style={containerStyle}>
        <div style={centreStyle}>
          <div style={spinnerStyle} />
          <p style={{ color: "var(--text-secondary)", marginTop: "1rem", fontSize: "0.95rem" }}>
            Computing {vizMethod.toUpperCase()} projection…
          </p>
        </div>
      </div>
    );
  }

  if (!vizData) {
    return (
      <div style={containerStyle}>
        <div style={centreStyle}>
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor"
            strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"
            style={{ color: "var(--border-hover)", marginBottom: "1rem" }}>
            <circle cx="12" cy="12" r="10" />
            <line x1="8" y1="12" x2="16" y2="12" />
            <line x1="12" y1="8" x2="12" y2="16" />
          </svg>
          <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
            Click <strong>Load Visualisation</strong> to project vectors into 3D space.
          </p>
          <button className="btn btn-primary btn-sm" onClick={onRefresh} style={{ marginTop: "1rem" }}>
            Load Visualisation
          </button>
        </div>
      </div>
    );
  }

  if (vizData.error) {
    return (
      <div style={containerStyle}>
        <div style={centreStyle}>
          <p style={{ color: "var(--danger-color)", fontWeight: 600 }}>⚠ {vizData.error}</p>
          <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginTop: "0.5rem" }}>
            Index at least 3 documents into this collection first.
          </p>
        </div>
      </div>
    );
  }

  const { points, variance_explained, n_docs } = vizData;

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>

      {/* ── Toolbar ── */}
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        flexWrap: "wrap",
        gap: "0.75rem",
        padding: "0.85rem 1.25rem",
        borderBottom: "1px solid var(--border-color)",
        background: "rgba(0,0,0,0.02)",
      }}>
        {/* Left: method toggle + doc count */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", fontWeight: 600 }}>Method:</span>
          {["pca", "tsne"].map(m => (
            <button
              key={m}
              onClick={() => onMethodChange(m)}
              style={{
                padding: "0.3rem 0.75rem",
                borderRadius: "5px",
                border: vizMethod === m ? "1px solid var(--accent-color)" : "1px solid var(--border-color)",
                background: vizMethod === m ? "var(--accent-glow)" : "transparent",
                color: vizMethod === m ? "var(--accent-color)" : "var(--text-secondary)",
                fontWeight: 600,
                fontSize: "0.78rem",
                cursor: "pointer",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                transition: "all 0.2s ease",
              }}
            >
              {m}
            </button>
          ))}
          <span style={{
            fontSize: "0.78rem",
            color: "var(--text-muted)",
            background: "var(--border-color)",
            padding: "0.2rem 0.5rem",
            borderRadius: "4px",
            fontFamily: "var(--font-mono)",
          }}>
            {n_docs} vectors
          </span>
        </div>

        {/* Right: variance explained (PCA only) + refresh */}
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          {variance_explained && (
            <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
              <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Variance:</span>
              {variance_explained.map((v, i) => (
                <span key={i} style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.72rem",
                  padding: "0.15rem 0.4rem",
                  borderRadius: "4px",
                  background: ["rgba(239,68,68,0.12)", "rgba(34,197,94,0.12)", "rgba(59,130,246,0.12)"][i],
                  color: ["#ef4444", "#22c55e", "#3b82f6"][i],
                  fontWeight: 600,
                }}>
                  PC{i + 1} {(v * 100).toFixed(1)}%
                </span>
              ))}
            </div>
          )}
          <button className="icon-btn" onClick={onRefresh} title="Reload">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
              strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="23 4 23 10 17 10" />
              <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
            </svg>
          </button>
        </div>
      </div>

      {/* ── Three.js Canvas ── */}
      {/* Outer: flex:1 gives the block room; inner: absolute fills it so R3F gets real px dimensions */}
      <div style={{ flex: 1, position: "relative", minHeight: "400px" }}>
        <div style={{ position: "absolute", inset: 0 }}>
          {/* Axis legend */}
          <div style={{
            position: "absolute",
            bottom: "12px",
            left: "14px",
            zIndex: 10,
            display: "flex",
            gap: "0.75rem",
            fontSize: "0.7rem",
            fontFamily: "var(--font-mono)",
            pointerEvents: "none",
          }}>
            {[["X", "#ef4444"], ["Y", "#22c55e"], ["Z", "#3b82f6"]].map(([ax, col]) => (
              <span key={ax} style={{ color: col, fontWeight: 700 }}>── {ax}</span>
            ))}
            <span style={{ color: "var(--text-muted)" }}>Drag to orbit · Scroll to zoom</span>
          </div>

          <Canvas
            camera={{ position: [4, 3, 5], fov: 60 }}
            gl={{ antialias: true, alpha: true }}
            style={{ width: "100%", height: "100%", background: "transparent" }}
          >
            <Suspense fallback={null}>
              <Scene points={points} />
            </Suspense>
          </Canvas>
        </div>
      </div>
    </div>
  );
}

// ─── Inline style constants ──────────────────────────────────────────────────
const containerStyle = {
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  minHeight: "420px",
  padding: "2rem",
};

const centreStyle = {
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  textAlign: "center",
  gap: "0.5rem",
};

const spinnerStyle = {
  width: "40px",
  height: "40px",
  border: "3px solid var(--border-color)",
  borderTop: "3px solid var(--accent-color)",
  borderRadius: "50%",
  animation: "spin 0.8s linear infinite",
};

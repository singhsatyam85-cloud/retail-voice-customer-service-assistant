import { useRef, useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";
import "./VoiceOrbDNA.css";

interface VoiceOrbDNAProps {
  state: "idle" | "listening" | "speaking" | "processing";
  size?: number;
  className?: string;
}

// Configuration for each state
const STATE_CONFIGS = {
  idle: {
    color: "#6366f1", // Indigo
    glowColor: "rgba(99, 102, 241, 0.15)",
    rotSpeed: 0.15,
    pulseSpeed: 1.0,
    waveAmp: 0.05,
    waveFreq: 4,
    zAmp: 0.05,
  },
  listening: {
    color: "#10b981", // Emerald green
    glowColor: "rgba(16, 185, 129, 0.25)",
    rotSpeed: 0.4,
    pulseSpeed: 3.5,
    waveAmp: 0.15,
    waveFreq: 6,
    zAmp: 0.18,
  },
  speaking: {
    color: "#f59e0b", // Amber
    glowColor: "rgba(245, 158, 11, 0.3)",
    rotSpeed: 0.6,
    pulseSpeed: 5.0,
    waveAmp: 0.22,
    waveFreq: 8,
    zAmp: 0.28,
  },
  processing: {
    color: "#8b5cf6", // Purple
    glowColor: "rgba(139, 92, 246, 0.2)",
    rotSpeed: 1.2,
    pulseSpeed: 2.0,
    waveAmp: 0.08,
    waveFreq: 12,
    zAmp: 0.1,
  },
};

const NUM_POINTS = 64;

function DnaHelix({ state }: { state: "idle" | "listening" | "speaking" | "processing" }) {
  const groupRef = useRef<THREE.Group>(null);
  const config = STATE_CONFIGS[state];

  // Helper arrays for points
  const theta = useMemo(() => {
    const arr = new Float32Array(NUM_POINTS);
    for (let i = 0; i < NUM_POINTS; i++) {
      arr[i] = (i / NUM_POINTS) * Math.PI * 2;
    }
    return arr;
  }, []);

  // Set initial geometries
  const [geomA, geomB, geomRungs, particleGeom] = useMemo(() => {
    const a = new THREE.BufferGeometry();
    const b = new THREE.BufferGeometry();
    const rungs = new THREE.BufferGeometry();

    const posA = new Float32Array(NUM_POINTS * 3);
    const posB = new Float32Array(NUM_POINTS * 3);
    const posRungs = new Float32Array(NUM_POINTS * 2 * 3); // 2 points per rung

    a.setAttribute("position", new THREE.BufferAttribute(posA, 3));
    b.setAttribute("position", new THREE.BufferAttribute(posB, 3));
    rungs.setAttribute("position", new THREE.BufferAttribute(posRungs, 3));

    // Particle field
    const particles = new THREE.BufferGeometry();
    const numParticles = 40;
    const particlePositions = new Float32Array(numParticles * 3);
    for (let i = 0; i < numParticles; i++) {
      const angle = Math.random() * Math.PI * 2;
      const r = 0.8 + Math.random() * 0.6;
      particlePositions[i * 3] = r * Math.cos(angle);
      particlePositions[i * 3 + 1] = r * Math.sin(angle);
      particlePositions[i * 3 + 2] = (Math.random() - 0.5) * 0.5;
    }
    particles.setAttribute("position", new THREE.BufferAttribute(particlePositions, 3));

    return [a, b, rungs, particles];
  }, []);

  // Create materials
  const [matA, matB, matRungs, matParticles] = useMemo(() => {
    const color = new THREE.Color(config.color);
    return [
      new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.8 }),
      new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.8 }),
      new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.4 }),
      new THREE.PointsMaterial({ color, size: 0.03, sizeAttenuation: true, transparent: true, opacity: 0.5 }),
    ];
  }, []);

  // Update materials when color changes
  useMemo(() => {
    const color = new THREE.Color(config.color);
    matA.color = color;
    matB.color = color;
    matRungs.color = color;
    matParticles.color = color;
  }, [config.color, matA, matB, matRungs, matParticles]);

  // Create three objects
  const [lineA, lineB, rungs, points] = useMemo(() => {
    return [
      new THREE.Line(geomA, matA),
      new THREE.Line(geomB, matB),
      new THREE.LineSegments(geomRungs, matRungs),
      new THREE.Points(particleGeom, matParticles),
    ];
  }, [geomA, geomB, geomRungs, particleGeom, matA, matB, matRungs, matParticles]);

  // Update positions in render loop
  useFrame(({ clock }) => {
    const time = clock.getElapsedTime();
    const posA = geomA.attributes.position.array as Float32Array;
    const posB = geomB.attributes.position.array as Float32Array;
    const posRungs = geomRungs.attributes.position.array as Float32Array;

    const R = 1.0; // Helix radius
    const waveAmp = config.waveAmp;
    const waveFreq = config.waveFreq;
    const zAmp = config.zAmp;
    const pulseSpeed = config.pulseSpeed;

    for (let i = 0; i < NUM_POINTS; i++) {
      const t = theta[i];
      // Wave modulation
      const wave = waveAmp * Math.sin(waveFreq * t + time * pulseSpeed);
      const zVal = zAmp * Math.cos(waveFreq * t + time * pulseSpeed);

      // Strand A
      const xA = (R + wave) * Math.cos(t);
      const yA = (R + wave) * Math.sin(t);
      const zA = zVal;

      posA[i * 3] = xA;
      posA[i * 3 + 1] = yA;
      posA[i * 3 + 2] = zA;

      // Strand B (opposite phase)
      const tB = t + Math.PI;
      const waveB = waveAmp * Math.sin(waveFreq * tB + time * pulseSpeed);
      const zValB = zAmp * Math.cos(waveFreq * tB + time * pulseSpeed);

      const xB = (R + waveB) * Math.cos(tB);
      const yB = (R + waveB) * Math.sin(tB);
      const zB = zValB;

      posB[i * 3] = xB;
      posB[i * 3 + 1] = yB;
      posB[i * 3 + 2] = zB;

      // Rungs connecting A to B
      posRungs[i * 6] = xA;
      posRungs[i * 6 + 1] = yA;
      posRungs[i * 6 + 2] = zA;

      posRungs[i * 6 + 3] = xB;
      posRungs[i * 6 + 4] = yB;
      posRungs[i * 6 + 5] = zB;
    }

    geomA.attributes.position.needsUpdate = true;
    geomB.attributes.position.needsUpdate = true;
    geomRungs.attributes.position.needsUpdate = true;

    // Slowly rotate the group
    if (groupRef.current) {
      groupRef.current.rotation.z += config.rotSpeed * 0.01;
      groupRef.current.rotation.y = Math.sin(time * 0.5) * 0.2;
    }
  });

  return (
    <group ref={groupRef}>
      <primitive object={lineA} />
      <primitive object={lineB} />
      <primitive object={rungs} />
      <primitive object={points} />
    </group>
  );
}

export function VoiceOrbDNA({ state, size = 120, className = "" }: VoiceOrbDNAProps) {
  const config = STATE_CONFIGS[state];

  return (
    <div
      className={`voice-orb-dna-container ${className}`}
      style={{
        width: size,
        height: size,
        "--glow-color": config.glowColor,
      } as React.CSSProperties}
    >
      <div className="voice-orb-dna__glow" />
      <Canvas
        camera={{ position: [0, 0, 2.5], fov: 60 }}
        gl={{ alpha: true, antialias: true }}
        style={{ background: "transparent" }}
      >
        <ambientLight intensity={1.5} />
        <DnaHelix state={state} />
      </Canvas>
    </div>
  );
}

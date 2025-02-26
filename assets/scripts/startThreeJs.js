/*модель*/
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(70, window.innerWidth / window.innerHeight, 0.1, 1000);

// Создаем рендерер с прозрачным фоном
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.getElementById('main').appendChild(renderer.domElement);

// Добавляем оси координат
const axesHelper = new THREE.AxesHelper(5);
scene.add(axesHelper);

const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
scene.add(ambientLight);

const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
directionalLight.position.set(5, 5, 5);
scene.add(directionalLight);

const loader = new THREE.GLTFLoader();

// Устанавливаем позицию камеры
camera.position.set(-10, 10, 18); // Камера находится под углом 45 градусов по оси Y


// Направляем камеру на центр сцены
camera.lookAt(0, 0, 0);

function animate() {
    requestAnimationFrame(animate);
    renderer.render(scene, camera);
}


window.addEventListener('wheel', (event) => {
    event.preventDefault();
    camera.position.z += event.deltaY * 0.01;
    camera.position.z = Math.max(1, camera.position.z);
}, { passive: false });

function animate() {
    requestAnimationFrame(animate);
    renderer.render(scene, camera);
}

window.addEventListener('resize', () => {
    const width = window.innerWidth;
    const height = window.innerHeight;

    renderer.setSize(width, height);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
});
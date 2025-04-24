/*Создание сцены*/
const mainElement = document.getElementById('main');
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(70, mainElement.clientWidth / mainElement.clientHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setSize(mainElement.clientWidth, mainElement.clientHeight);
mainElement.appendChild(renderer.domElement);
/*Освещение*/
const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
scene.add(ambientLight);
const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
directionalLight.position.set(5, 5, 5);
scene.add(directionalLight);
const loader = new THREE.GLTFLoader();
/*остановка генерации в зависимоти поведения пользователя*/
camera.position.set(-5, 7, 10.5);
camera.lookAt(0, 0, 0);

function animate() {
    requestAnimationFrame(animate);
    renderer.render(scene, camera);
}
animate();
/*создание моделей каркасы*/
let models = {};
let model;
let olderPCModel, speakerModel, serverModel, CafetalgModel, PanasonicModel, ScifiSciderRobotModel, TheGlobeModel,
    DrinkingWaterDispenserModel, HumanoidRobotModel, ComputerWithTerminalModel, ConditionerModel, FridgeModel,
    PS5Model, TVModel, CoolerModel, ShowcaseModel, PrinterModel, RadioModel, MacbookModel;
/*обновление баланса в зависимости от предмета*/
function updateTotalGeneration(itemName) {
    const items = {
        "Older PC": olderPC,
        "Speaker": speaker,
        "Server": server,
        "Cafetalg": cafetalg,
        "Panasonic": panasonic,
        "Scifi Scider Robot": scifisciderrobot,
        "The Globe": theglobe,
        "Drinking Water Dispenser": drinkingWaterDispenser,
        "Humanoid robot": humanoidRobot,
        "Computer with terminal": computerWithTerminal,
        "Conditioner": conditioner,
        "Fridge": fridge,
        "PS5": ps5,
        "TV": tv,
        "Cooler": cooler,
        "Showcase": showcase,
        "Printer": printer,
        "Radio": radio,
        "Macbook": macbook
    };
    if (items[itemName] && !models[itemName]) {
        items[itemName]();
        models[itemName] = true;
    }
}
/*модель офиса как основа*/
loader.load('/static/models/Office.glb', function (gltf) {
    model = gltf.scene;
    model.scale.set(0.95, 0.95, 0.95);
    model.position.set(3.5, 0.5, 0);
    scene.add(model);
    model.rotateY(Math.PI);
    animate();
}, undefined, function (error) {
    console.error('Ошибка загрузки модели офиса:', error);
});
/*модели и их параметры в сетке внутри офиса, позиции, доступность и размер и генерация в сцене*/
function olderPC() { if (!olderPCModel) loader.load('/static/models/RetroPC.glb', gltf => { olderPCModel = gltf.scene; olderPCModel.scale.set(0.014, 0.014, 0.014); olderPCModel.position.set(-2.7, 0.2, -2.5); scene.add(olderPCModel); }); }
function speaker() { if (!speakerModel) loader.load('/static/models/Speaker.glb', gltf => { speakerModel = gltf.scene; speakerModel.scale.set(0.001, 0.001, 0.001); speakerModel.position.set(-1, 0.2, -2.8); scene.add(speakerModel); }); }
function server() { if (!serverModel) loader.load('/static/models/ServerV2+console.glb', gltf => { serverModel = gltf.scene; serverModel.scale.set(0.2, 0.2, 0.2); serverModel.position.set(0.2, 0.2, -2.8); scene.add(serverModel); }); }
function cafetalg() { if (!CafetalgModel) loader.load('/static/models/CAFETALG.glb', gltf => { CafetalgModel = gltf.scene; CafetalgModel.scale.set(0.00010, 0.00010, 0.00010); CafetalgModel.position.set(1.5, 0.2, -2.8); scene.add(CafetalgModel); }); }
function panasonic() { if (!PanasonicModel) loader.load('/static/models/Panasonic.glb', gltf => { PanasonicModel = gltf.scene; PanasonicModel.scale.set(1, 1, 1); PanasonicModel.position.set(-0.6, 0.5, 1); scene.add(PanasonicModel); }); }
function scifisciderrobot() { if (!ScifiSciderRobotModel) loader.load('/static/models/ScifiSciderRobot.glb', gltf => { ScifiSciderRobotModel = gltf.scene; ScifiSciderRobotModel.scale.set(0.2, 0.2, 0.2); ScifiSciderRobotModel.position.set(-1.9, 0.5, 1); scene.add(ScifiSciderRobotModel); }); }
function theglobe() { if (!TheGlobeModel) loader.load('/static/models/TheGlobe.glb', gltf => { TheGlobeModel = gltf.scene; TheGlobeModel.scale.set(0.3, 0.3, 0.3); TheGlobeModel.position.set(-3.2, 0.5, 1); scene.add(TheGlobeModel); }); }
function drinkingWaterDispenser() { if (!DrinkingWaterDispenserModel) loader.load('/static/models/Drinking Water Dispenser.glb', gltf => { DrinkingWaterDispenserModel = gltf.scene; DrinkingWaterDispenserModel.scale.set(0.02, 0.02, 0.02); DrinkingWaterDispenserModel.position.set(-2.7, 0.2, -4); scene.add(DrinkingWaterDispenserModel); }); }
function humanoidRobot() { if (!HumanoidRobotModel) loader.load('/static/models/Humanoid robot.glb', gltf => { HumanoidRobotModel = gltf.scene; HumanoidRobotModel.scale.set(0.9, 0.9, 0.9); HumanoidRobotModel.position.set(-1.3, 0.2, -3.8); scene.add(HumanoidRobotModel); }); }
function computerWithTerminal() { if (!ComputerWithTerminalModel) loader.load('/static/models/Computer with terminal.glb', gltf  => { ComputerWithTerminalModel = gltf.scene; ComputerWithTerminalModel.scale.set(0.5, 0.5, 0.5); ComputerWithTerminalModel.position.set(0, 0.2, -3.8); scene.add(ComputerWithTerminalModel); }); }
function conditioner() { if (!ConditionerModel) loader.load('/static/models/Conditioner.glb', gltf => { ConditionerModel = gltf.scene; ConditionerModel.scale.set(0.040, 0.040, 0.040); ConditionerModel.position.set(1.7, 0.7, -3.8); ConditionerModel.rotateY(Math.PI / 2); scene.add(ConditionerModel); }); }
function fridge() { if (!FridgeModel) loader.load('/static/models/Fridge.glb', gltf => { FridgeModel = gltf.scene; FridgeModel.scale.set(0.9, 0.9, 0.9); FridgeModel.position.set(2.8, 0, -3.6); scene.add(FridgeModel); }); }
function ps5() { if (!PS5Model) loader.load('/static/models/PS5.glb', gltf => { PS5Model = gltf.scene; PS5Model.scale.set(2, 2, 2); PS5Model.position.set(2.8, 0.2, -2.5); scene.add(PS5Model); }); }
function tv() { if (!TVModel) loader.load('/static/models/TV.glb', gltf => { TVModel = gltf.scene; TVModel.scale.set(0.0010, 0.0010, 0.0010); TVModel.position.set(1.3, 0.2, 1); scene.add(TVModel); }); }
function cooler() { if (!CoolerModel) loader.load('/static/models/Cooler.glb', gltf => { CoolerModel = gltf.scene; CoolerModel.scale.set(0.03, 0.03, 0.03); CoolerModel.position.set(0.3, 0.2, 2.1); scene.add(CoolerModel); }); }
function showcase() { if (!ShowcaseModel) loader.load('/static/models/Showcase.glb', gltf => { ShowcaseModel = gltf.scene; ShowcaseModel.scale.set(0.005, 0.005, 0.005); ShowcaseModel.position.set(2.8, 0.2, 1); ShowcaseModel.rotation.y = -Math.PI / 2; scene.add(ShowcaseModel); }); }
function printer() { if (!PrinterModel) loader.load('/static/models/Printer.glb', gltf => { PrinterModel = gltf.scene; PrinterModel.scale.set(0.002, 0.002, 0.002); PrinterModel.position.set(-3, 0.5, 2.1); PrinterModel.rotation.y = Math.PI / 2; scene.add(PrinterModel); }); }
function radio() { if (!RadioModel) loader.load('/static/models/Radio.glb', gltf => { RadioModel = gltf.scene; RadioModel.scale.set(0.6, 0.6, 0.6); RadioModel.position.set(-1.3, 0.2, 1.7); scene.add(RadioModel); }); }
function macbook() {
    if (!MacbookModel) loader.load('/static/models/macbook.glb', gltf => {
        MacbookModel = gltf.scene;
        MacbookModel.scale.set(0.1, 0.1, 0.1);
        MacbookModel.position.set(1.5, 0.2, 2.1);
        scene.add(MacbookModel);
    }, undefined, function (error) {
        console.error('Ошибка загрузки модели макбука:', error);
    });
}
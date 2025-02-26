let model;
let hasOlderPC = false;
let hasSpeaker = false;
let hasServer = false;
let hasCafetalg = false;
let hasPanasonic = false;
let hasScifiSciderRobot = false;
let hasTheGlobe = false;

let olderPCModel = null;
let speakerModel = null;
let serverModel = null;

let CafetalgModel = null;
let PanasonicModel = null;
let ScifiSciderRobotModel = null;
let TheGlobeModel = null;

// Загрузка модели офиса
loader.load('assets/models/Office.glb', function (gltf) {
    model = gltf.scene;
    model.scale.set(0.95, 0.95, 0.95);
    model.position.set(3.5, 0.5, 0);
    scene.add(model);

    model.rotateY(Math.PI);

    animate();
}, undefined, function (error) {
    console.error('Ошибка загрузки модели офиса:', error);
});

function olderPC() {
    if (!hasOlderPC || olderPCModel !== null) return;

    loader.load('assets/models/RetroPC.glb', function (pcGltf) {
        olderPCModel = pcGltf.scene;
        olderPCModel.scale.set(0.014, 0.014, 0.014);
        olderPCModel.position.set(-2.7, 0.5, -2.5);
        scene.add(olderPCModel);
    }, undefined, function (error) {
        console.error('Ошибка загрузки модели "Older PC":', error);
    });
}

function speaker() {
    if (!hasSpeaker || speakerModel !== null) return;

    loader.load('assets/models/Speaker.glb', function (spGltf) {
        speakerModel = spGltf.scene;
        speakerModel.scale.set(0.001, 0.001, 0.001);
        speakerModel.position.set(-1, 0.5, -2.8);
        scene.add(speakerModel);
    }, undefined, function (error) {
        console.error('Ошибка загрузки модели "Speaker":', error);
    });
}

function server() {
    if (!hasServer || serverModel !== null) return;

    loader.load('assets/models/ServerV2+console.glb', function (serverGltf) {
        serverModel = serverGltf.scene;
        serverModel.scale.set(0.2, 0.2, 0.2);
        serverModel.position.set(0.5, 0.5, -2.8);
        scene.add(serverModel);
    }, undefined, function (error) {
        console.error('Ошибка загрузки модели "Server":', error);
    });
}

function cafetalg() {
    if (!hasCafetalg || CafetalgModel !== null) return;

    loader.load('assets/models/CAFETALG.glb', function (cafetalgGltf) {
        CafetalgModel = cafetalgGltf.scene;
        CafetalgModel.scale.set(10, 10, 10);
        CafetalgModel.position.set(0.5, 0.5, -2.8);
        scene.add(CafetalgModel);
    }, undefined, function (error) {
        console.error('Ошибка загрузки модели "Cafetalg":', error);
    });
    
}

function panasonic() {
   if (!hasPanasonic || PanasonicModel !== null) return;

    loader.load('assets/models/Panasonic.glb', function (panasonicGltf) {
        PanasonicModel = panasonicGltf.scene;
        PanasonicModel.scale.set(1, 1, 1);
        PanasonicModel.position.set(-0.6, 0.5, 1);
        scene.add(PanasonicModel);
    }, undefined, function (error) {
        console.error('Ошибка загрузки модели "Panasonic":', error);
    });
    
}

function scifisciderrobot() {
    if (!hasScifiSciderRobot || ScifiSciderRobotModel !== null) return;

    loader.load('assets/models/ScifiSciderRobot.glb', function (scifisciderrobotgGltf) {
        ScifiSciderRobotModel = scifisciderrobotgGltf.scene;
        ScifiSciderRobotModel.scale.set(0.2, 0.2, 0.2);
        ScifiSciderRobotModel.position.set(-1.9, 0.5, 1);
        scene.add(ScifiSciderRobotModel);
    }, undefined, function (error) {
        console.error('Ошибка загрузки модели "ScifiSciderRobot":', error);
    });
}

function theglobe() {
    if (!hasTheGlobe || TheGlobeModel !== null) return;

    loader.load('assets/models/TheGlobe.glb', function (theglobegGltf) {
        TheGlobeModel = theglobegGltf.scene;
        TheGlobeModel.scale.set(0.3, 0.3, 0.3);
        TheGlobeModel.position.set(-3.2, 0.5, 1);
        scene.add(TheGlobeModel);
    }, undefined, function (error) {
        console.error('Ошибка загрузки модели "TheGlobe":', error);
    });
}



function changeColor() {
    if (document.querySelector("#month-calendar") != null) {
        var element = document.querySelector("#month-calendar");
    } else if (document.querySelector("#year-calendar") != null) {
        var element = document.querySelector("#year-calendar");
    } else if (document.querySelector("#week-calendar") != null) {
        var element = document.querySelector("#week-calendar");
    } else if (document.querySelector("#day-calendar") != null) {
        var element = document.querySelector("#day-calendar");
    }

    var color = setCalendarColor(element.className);
    document.documentElement.style.setProperty('--month-color', color);
    document.documentElement.style.setProperty('--var-color', color);
    return;
};

function setCalendarColor(element) {
    var dict = {
        0: "#32a6d7",
        1: "#3074b3",
        2: "#8869ac",
        3: "#b867ac",
        4: "#eb65ae",
        5: "#ee474e",
        6: "#f48c4d",
        7: "#f9a44a",
        8: "#fdcd3d",
        9: "#fef432",
        10: "#a2fc38",
        11: "#33b8a5"
    };

    return dict[element % 12];
};

changeColor();



function toggleFilter(button) {
    button.classList.toggle('active');
}

function restrictiveToggleFilter(buttonIdList) {
    const firstButtonId = buttonIdList[0];
    
    const firstButton = document.getElementById(firstButtonId);
    firstButton.classList.add('active');

    buttonIdList.slice(1).forEach(otherButtonId => {
        const otherButton = document.getElementById(otherButtonId);
        otherButton.classList.remove('active');
    });
}
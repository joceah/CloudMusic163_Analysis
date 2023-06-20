// 获取所有类名为card的元素
let cards = document.getElementsByClassName("card")
 
// 设置定时器，每1000毫秒调用依次showCard()函数
let i = setInterval("showCard()", 1000)
// 延时函数
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  } 
// 根据全局变量index值来依次显示
let index = 0

async function showCard() {
    await sleep (2000);
    cards[index].style.opacity = 1
    index++
    if (index == cards.length) {
        clearInterval(i)
        index = 0
    }
}

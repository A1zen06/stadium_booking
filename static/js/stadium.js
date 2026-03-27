$(document).ready(function() {
    // Маска для телефона
    $('.phone-mask').mask('+7 (000) 000-00-00');
    
    // Автоматическое скрытие сообщений через 5 секунд
    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 5000);
    
    // Плавная прокрутка
    $('a[href*="#"]').click(function(e) {
        if (this.hash !== '') {
            e.preventDefault();
            let hash = this.hash;
            $('html, body').animate({
                scrollTop: $(hash).offset().top
            }, 500);
        }
    });
    
    // Анимация при наведении на карточки
    $('.card').hover(
        function() {
            $(this).css('transform', 'translateY(-5px)');
        },
        function() {
            $(this).css('transform', 'translateY(0)');
        }
    );
});
// Прижимаем футер к низу
function fixFooter() {
    var body = document.body;
    var html = document.documentElement;
    var footer = document.querySelector('footer');
    
    if (!footer) return;
    
    var height = Math.max(body.scrollHeight, body.offsetHeight, 
                          html.clientHeight, html.scrollHeight, html.offsetHeight);
    
    if (height < window.innerHeight) {
        footer.style.position = 'fixed';
        footer.style.bottom = '0';
        footer.style.left = '0';
        footer.style.right = '0';
        footer.style.width = '100%';
    } else {
        footer.style.position = 'static';
    }
}

// Запускаем при загрузке и при изменении размера окна
window.addEventListener('load', fixFooter);
window.addEventListener('resize', fixFooter);
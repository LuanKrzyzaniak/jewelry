function setupDecimalMask(input, decimals) {
    let digits = [];

    function update() {
        if (digits.length === 0) {
            input.value = '0,' + '0'.repeat(decimals);
            return;
        }
        const padded = digits.join('').padStart(decimals + 1, '0');
        const intPart = parseInt(padded.slice(0, padded.length - decimals), 10).toString();
        const decPart = padded.slice(padded.length - decimals);
        input.value = intPart + ',' + decPart;
    }

    function initFromExisting(val) {
        if (!val) return;
        const normalized = val.replace(',', '.');
        const num = parseFloat(normalized);
        if (isNaN(num) || num === 0) return;
        const intVal = Math.round(num * Math.pow(10, decimals)).toString();
        digits = intVal.split('');
    }

    initFromExisting(input.value);
    update();

    input.addEventListener('keydown', (e) => {
        if (e.key >= '0' && e.key <= '9') {
            e.preventDefault();
            digits.push(e.key);
            update();
        } else if (e.key === 'Backspace') {
            e.preventDefault();
            digits.pop();
            update();
        } else if (e.key === 'Delete') {
            e.preventDefault();
            digits = [];
            update();
        }
    });

    input.addEventListener('paste', (e) => {
        e.preventDefault();
        const text = (e.clipboardData || window.clipboardData).getData('text');
        const nums = text.replace(/[^0-9]/g, '');
        if (nums) {
            digits = nums.replace(/^0+/, '').split('') || [];
            update();
        }
    });

    input.closest('form')?.addEventListener('submit', () => {
        input.value = input.value.replace(',', '.');
    });
}

function setupDateMask(input) {
    function isoParaBr(val) {
        const m = val.match(/^(\d{4})-(\d{2})-(\d{2})$/);
        return m ? `${m[3]}/${m[2]}/${m[1]}` : val;
    }

    function brParaIso(val) {
        const m = val.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
        return m ? `${m[3]}-${m[2]}-${m[1]}` : val;
    }

    if (input.value) input.value = isoParaBr(input.value);

    input.addEventListener('input', () => {
        let digits = input.value.replace(/\D/g, '').slice(0, 8);
        let out = digits;
        if (digits.length > 4) out = digits.slice(0,2) + '/' + digits.slice(2,4) + '/' + digits.slice(4);
        else if (digits.length > 2) out = digits.slice(0,2) + '/' + digits.slice(2);
        input.value = out;
    });

    input.closest('form')?.addEventListener('submit', () => {
        input.value = brParaIso(input.value);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-mask="decimal-2"]').forEach(el => setupDecimalMask(el, 2));
    document.querySelectorAll('[data-mask="decimal-3"]').forEach(el => setupDecimalMask(el, 3));
    document.querySelectorAll('[data-mask="decimal-4"]').forEach(el => setupDecimalMask(el, 4));
    document.querySelectorAll('[data-mask="date"]').forEach(el => setupDateMask(el));
});
